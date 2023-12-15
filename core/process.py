from collections import deque, Counter, defaultdict
import networkx as nx
from dataclasses import fields, dataclass
from typing_extensions import Self
from typing import overload, Any, Union
from numbers import Number
from functools import singledispatchmethod

import numpy as np
from scipy.optimize import linprog

from core.material import MaterialSpec

def dataclass_to_list(dc):
    return [getattr(dc, f.name) for f in fields(dc)]

class _SignalClass:
    """
    Used for single dispatch on Self type
    """

@dataclass(frozen=True)
class ProcessNode(_SignalClass):
    name: str  # TODO: use an enum of node types, rather than names, to make plotting easier
    input_materials: MaterialSpec
    output_materials: MaterialSpec
    power_production: float
    power_consumption: float

    def __repr__(self) -> str:
        ingredients = " ".join(repr(self.input_materials).splitlines())
        products = " ".join(repr(self.output_materials).splitlines())

        return f"{ingredients} >> {products}"

    @singledispatchmethod
    def __rshift__(self, other: Any) -> Self | MaterialSpec:
        """
        self >> other
        """
        return NotImplemented

    @__rshift__.register
    def _(self, other: MaterialSpec) -> MaterialSpec:
        scale = other // self.output_materials
        return self.input_materials * scale

    @__rshift__.register(_SignalClass)
    def _(self, other: Self) -> Self:
        return CompositeProcessNode(self, other)

    @singledispatchmethod
    def __lshift__(self, other: Any) -> Self | MaterialSpec:
        """
        Solve for outputs or join process nodes
        self << other 
        """
        return NotImplemented

    @__lshift__.register
    def _(self, other: MaterialSpec) -> MaterialSpec:
        scale = self.input_materials // other
        return self.output_materials * scale

    @__lshift__.register(_SignalClass)
    def _(self, other: Self) -> Self:
        return CompositeProcessNode(other, self)

    def __rrshift__(self, other: Self | MaterialSpec | Any) -> Self | MaterialSpec:
        """
        Solve for inputs or join process nodes
        other >> self 
        """
        return self << other 

    def __rlshift__(self, other: Self | MaterialSpec | Any) -> Self | MaterialSpec:
        """
        Solve for outputs
        other << self
        """
        return self >> other 

    def __mul__(self, scalar: float) -> Self:
        """
        Scale up this recipe
        """
        return type(self)(self.name, self.input_materials * scalar, self.output_materials * scalar, self.power_production * scalar, self.power_consumption * scalar)

    def has_input(self, material: str) -> bool:
        return getattr(self.input_materials, material) > 0

    def has_output(self, material: str) -> bool:
        return getattr(self.output_materials, material) > 0


class CompositeProcessNode(ProcessNode):
    """
    ProcessNode that wraps other process nodes. Does not encode specific connections between process nodes. 
    Rather, pools resources to create a net in and out flow. This creates process pipelines rather than process
    graphs. These are suitable for abstracting away network details for use as nodes in larger optimizations or
    calculating material throughput, but not for optimizing network topology.
    """
    nodes: set[ProcessNode]

    def __init__(self, *nodes: ProcessNode) -> None:
        # TODO: make empty materials
        empty = nodes[0].input_materials.empty()  # FIXME: why
        sum_inputs = sum((node.input_materials for node in nodes), empty)
        sum_outputs = sum((node.output_materials for node in nodes), empty)

        net_inputs = (sum_inputs - (sum_outputs | sum_inputs)) > 0
        net_outputs = (sum_outputs - (sum_inputs | sum_outputs)) > 0

        power_production = sum(node.power_production for node in nodes)
        power_consumption = sum(node.power_consumption for node in nodes)
        self.nodes = set(nodes)

        super().__init__(name="Composite", input_materials=net_inputs, output_materials=net_outputs,power_production=power_production, power_consumption=power_consumption)


class Process(CompositeProcessNode):
    """
    Store graph as adjacency matrix, no real value in adjacency list here because optimization runs on the full graph
    rather than traversal. This also saves us from the issue of binding a ProcessNodes to Optimization instances
    1:1, since it may be useful to re-use the same CompositeProcessNode, representing a factory, in multiple
    different contexts or optimizations. Representing the graph this way saves us from needing an additional
    intermediate class or modifying nodes.

    # TODO: save solution to Process
    """

    def __init__(self, process_graph: nx.MultiGraph) -> None:
        # TODO: create duing init, requires ability to add source/sink nodes in optimization
        self.graph = process_graph

    @classmethod
    def _filter_eligible_nodes(cls, output_node: ProcessNode, available_nodes: list[ProcessNode]) -> list[ProcessNode]:
        graph = cls._make_graph([output_node] + available_nodes)
        return nx.ancestors(graph, output_node) | {output_node}

    @staticmethod
    def _make_graph(nodes: list[ProcessNode]) -> nx.MultiGraph:
        graph = nx.MultiGraph()
        graph.add_nodes_from(nodes)

        for i, node_1 in enumerate(nodes):
            for node_2 in nodes[i:]:
                # TODO: add all materials as attributes to node
                # TODO: add scale attribute to node
                # TODO: add cost attribute to node
                if any(v for _, v in node_1.input_materials | node_2.output_materials):
                    graph.add_edge(node_1, node_2)
                if any(v for _, v in node_2.input_materials | node_1.output_materials):
                    graph.add_edge(node_2, node_1)

        return graph

    @classmethod
    def minimize_input(cls, target_output: MaterialSpec, process_nodes: list[ProcessNode],include_power=False):
        """
        Find the weights on process nodes that produce the desired output with the least input and
        process cost.
        
        # TODO: availability constraints
        """
        output = ProcessNode("Output", target_output, target_output, 0, 0)

        connected_nodes = cls._filter_eligible_nodes(output, process_nodes + [output])
        costs = [1 for _ in connected_nodes]  # TODO: cost per recipe
        output_lower_bound = np.array(dataclass_to_list(target_output))

        # matrix where each machine is a column and each material is a row
        material_constraints = np.array(
            [dataclass_to_list(node.output_materials - node.input_materials) + ([node.power_consumption - node.power_production] if include_power else []) for node in connected_nodes]).T

        # use -1 factor to convert problem of materials * coeefficients >= outputs to minimization
        # production >= target
        bounds = (0, None)
        solution = linprog(c=costs, A_ub=material_constraints * -1, b_ub=output_lower_bound * -1, bounds = bounds)

        # temporary during testing
        return solution

    @classmethod
    def maximize_output(cls, available_materials: MaterialSpec, target_output: MaterialSpec, process_nodes: list[ProcessNode], include_power=False):
        """
        Maximize production of output materials where input materials are constrained. If extractors
        are allowed, problem may be unbounded due to unlimited material supply. This may be addressed
        by future work that constrains extractors by total available supply or changes how extractor
        cost is modelled.
        """
        output = ProcessNode("Output", target_output, target_output, 0, 0)

        visited = cls._filter_eligible_nodes(output, process_nodes + [output])

        # small penalty for using machines, to avoid creating redundant loops, reward for producing
        # more output
        costs = [-1 if node is output else .0001 for node in visited]  # TODO: cost per recipe

        # matrix where each machine is a column and each material is a row
        material_constraints = np.array(
            [dataclass_to_list(node.output_materials - node.input_materials) for node in visited]).T

        material_consumption_upper_bound = dataclass_to_list(available_materials)

        # production_rows = np.nonzero(dataclass_to_list(target_output))

        # material_constraints[production_rows] *= -1

        # consumption <= available
        # byproducts >= 0
        bounds = (0, None)

        solution = linprog(c=costs,
                           A_ub=material_constraints,
                           b_ub=material_consumption_upper_bound)

        # temporary during testing
        breakpoint()
        return solution

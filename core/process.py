from collections import deque, Counter
from dataclasses import fields, dataclass
from typing_extensions import Self
from typing import overload, Any
from numbers import Number
from functools import singledispatch

import numpy as np
from scipy.optimize import linprog

# Deprecated
from core.machine import Machine
from core.recipe import Recipe

from core.material import MaterialSpec

def dataclass_to_list(dc):
    return [getattr(dc, f.name) for f in fields(dc)]


@dataclass
class ProcessNode:
    name: str  # TODO: use an enum of node types, rather than names, to make plotting easier
    input_materials: MaterialSpec
    output_materials: MaterialSpec
    power: float

    def __repr__(self) -> str:
        ingredients = " ".join(repr(self.input_materials).splitlines())
        products = " ".join(repr(self.output_materials).splitlines())

        return f"{ingredients} >> {products}"

    @singledispatch
    def __rshift__(self, other: Any) -> CompositeProcessNode | MaterialSpec:
        """
        self >> other
        """
        return NotImplemented

    @__rshift__.register
    def _(self, other: MaterialSpec) -> MaterialSpec:
        scale = other // self.output_materials
        return self.input_materials * scale

    @__rshift__.register
    def _(self, other: "ProcessNode") -> CompositeProcessNode:
        return CompositeProcessNode(self, other)

    @singledispatch
    def __lshift__(self, other: Any) -> CompositeProcessNode | MaterialSpec:
        """
        Solve for outputs or join process nodes
        self << other 
        """
        return NotImplemented

    @__lshift__.register
    def _(self, other: MaterialSpec) -> MaterialSpec:
        scale = self.input_materials // other
        return self.output_materials * scale

    @__lshift__.register
    def _(self, other: "ProcessNode") -> CompositeProcessNode:
        return CompositeProcessNode(other, self)

    def __rrshift__(self, other: "ProcessNode" | MaterialSpec | Any) -> "ProcessNode" | MaterialSpec:
        """
        Solve for inputs or join process nodes
        MaterialSpec << Recipe
        """
        return self << other 

    def __llshift__(self, other: "ProcessNode" | MaterialSpec | Any) -> "ProcessNode" | MaterialSpec:
        """
        Solve for outputs
        MaterialSpec >> Recipe
        """
        return self >> other 

    def __mul__(self, scalar: float) -> Self:
        """
        Scale up this recipe
        """
        return type(self)(self.name, self.ingredients * scalar, self.products * scalar)

    def __rtruediv__(self, material_spec: MaterialSpec) -> Number:
        """
        Get the number of iterations of this recipe that can be produced from the given material_spec
        """
        return self.input_materials / material_spec

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
        sum_inputs = sum(node.input_materials for node in nodes)
        sum_outputs = sum(node.output_materials for node in nodes)

        net_inputs = (sum_inputs - (sum_outputs | sum_inputs)) > 0
        net_outputs = (sum_outputs - (sum_inputs | sum_outputs)) > 0

        power = sum(node.power for node in nodes)
        self.nodes = set(nodes)

        super().__init__(input_materials=net_inputs, output_materials=net_outputs, power=power)


class ProcessOptimization:
    """
    Store graph as adjacency matrix, no real value in adjacency list here because optimization runs on the full graph
    rather than traversal. This also saves us from the issue of binding a ProcessNodes to Optimization instances
    1:1, since it may be useful to re-use the same CompositeProcessNode, representing a factory, in multiple
    different contexts or optimizations. Representing the graph this way saves us from needing an additional
    intermediate class or modifying nodes.
    """

    @classmethod
    def from_outputs(cls, target_output: MaterialSpec, machines: list[ProcessNode], include_power=False):
        """
        Builds a process tree from a list of machines

        TODO: co-optimize generation, use less than constraint, multiple gen/load by -1 to ensure excess consumption
        TODO: allow surplos
        """
        output = Machine(Recipe("output", target_output, target_output, duration=1))
        nodes = deque([output])
        visited = set()
        registry = {}

        # collect possible nodes in tree
        while len(nodes):
            current_node = nodes.popleft()
            visited.add(current_node)

            for machine in machines:
                for ingredient in current_node.ingredients():
                    if machine.has_output(ingredient):
                        if machine not in visited:
                            nodes.append(machine)

        visited = list(visited)
        costs = [1 for _ in visited]  # TODO: pre-process cost per recipe
        output_equals = dataclass_to_list(target_output)

        material_constraints = np.array(
            [dataclass_to_list(m.recipe.products - m.recipe.ingredients) for m in visited]).T

        if include_power:
            A_ub = [m.power_consumption - m.power_production for m in visited]
            b_ub = [0]
            solution = linprog(c=costs, A_eq=material_constraints, b_eq=output_equals, A_ub=A_ub, b_ub=b_ub)
        else:
            solution = linprog(c=costs, A_eq=material_constraints, b_eq=output_equals)

        if solution.x is None:
            raise RuntimeError(solution)

        for m, s in zip(visited, solution.x.round(4)):
            cls(m, registry, s)

        cls(output, registry, 1)

        return registry[output]

    @classmethod
    def from_inputs(cls, available_materials: MaterialSpec, target_output: MaterialSpec, process_nodes: list[ProcessNode], include_power=False):
        """
        NOTE: if extractors are passed in here, this optimization is unbounded, since extractors are currently modelled as requiring no resources
              to output their expected output. This may be why extractors in the config have a balanced in and output rate. In the case of this
              problem, however, the optimizer will ignore extractors since consuming materials directly is equivalent.
              FIXME: this can be addressed by adding an additional constraint on producers/extractors. May be trick for intermediate products
        """
        inputs = Machine(Recipe("input", available_materials, available_materials, duration=1))
        nodes = deque([inputs])
        visited = set()
        registry = {}

        # collect possible nodes in tree
        while len(nodes):
            current_node = nodes.popleft()
            visited.add(current_node)
            for machine in machines:
                for product in current_node.products():
                    # TODO: this works, for unknown reasons. Without this, solution includes extraneous recipes, seemingly
                    # to balance consumption
                    if machine.has_input(product):
                        if machine not in visited:
                            nodes.append(machine)

        visited = list(visited)

        # FIXME: this setup of getattrs/weird loop order is heinous, even by the standards of this project
        costs = np.array([*[sum(
            (getattr(target_output, mat) > 0) * getattr(m.recipe.ingredients - m.recipe.products, mat) for mat in
            [*m.products(), *m.ingredients()]) for m in visited], *[.001 for _ in visited]])

        connect_eq_constraints = [
            [(j == i % len(visited)) * (1 - 2 * (i // len(visited))) for i, _ in enumerate([*visited, *visited])] for
            j, _ in enumerate(visited)]
        connect_eq_bounds = [0 for _ in range(len(visited))]

        production_matrix = np.array([dataclass_to_list(m.recipe.ingredients - m.recipe.products) for m in visited]).T
        production_matrix = np.concatenate((production_matrix, np.zeros_like(production_matrix)), axis=1)

        production_amounts = dataclass_to_list(target_output)
        production_indices, *_ = np.nonzero(production_amounts)

        for mat_1_idx, mat_2_idx in zip(production_indices[:-1], production_indices[1:]):
            ratio = production_amounts[mat_1_idx] / production_amounts[mat_2_idx]
            connect_eq_constraints.append(
                -1 * production_matrix[mat_1_idx, :] + ratio * production_matrix[mat_2_idx, :])
            connect_eq_bounds.append(0)

        connect_eq_constraints = np.array(connect_eq_constraints)
        connect_eq_bounds = np.array(connect_eq_bounds)

        # make products hove positive value, require consumption to be <= available
        output_bounds = np.array([*[material - .001 * (i in production_indices) for i, material in
                                    enumerate(dataclass_to_list(available_materials))]])

        solution = linprog(c=costs, A_ub=production_matrix, b_ub=output_bounds, A_eq=connect_eq_constraints,
                           b_eq=connect_eq_bounds)

        for m, s in zip(visited, solution.x.round(4)):
            cls(m, registry, s)

        cls(inputs, registry, 1)

        return registry[inputs]


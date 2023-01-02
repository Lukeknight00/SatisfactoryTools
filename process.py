from collections import deque
from dataclasses import fields

import numpy as np
from scipy.optimize import linprog

from machine import Machine
from material import MaterialSpec
from recipe import Recipe


def dataclass_to_list(dc):
    return [getattr(dc, f.name) for f in fields(dc)]


class Process:
    scale: int
    power: float = 0
    process_root: Machine
    input_materials: MaterialSpec
    output_materials: MaterialSpec

    def __init__(self, process_root: Machine, registry, scale: float = 1):
        self.process_root = process_root
        self.scale = scale
        self.input_materials = process_root.recipe.ingredients * scale
        self.output_materials = process_root.recipe.products * scale

        # TODO: this is terrible
        self.process_registry = registry
        registry[process_root] = self

    # TODO: limit materials as well as machines to optimize solver

    @classmethod
    def from_outputs(cls, target_output: MaterialSpec, machines: list[Machine], include_power=False):
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

        for m, s in zip(visited, solution.x.round(4)):
            cls(m, registry, s)

        cls(output, registry, 1)

        return registry[output]

    @classmethod
    def from_inputs(cls, available_materials, target_output, machines, generators=None):
        """
        NOTE: if extractors are passed in here, this optimization is unbounded, since extractors are currently modelled as requiring no resources
              to output their expected output. This may be why extractors in the config have a balanced in and output rate. In the case of this
              problem, however, the optimizer will ignore extractors since consuming materials directly is equivalent.
              FIXME: this can be addressed by adding an additional constraint on producers/extractors. May be trick for intermediate products
        """
        inputs = Machine(Recipe("input", available_materials, available_materials))
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

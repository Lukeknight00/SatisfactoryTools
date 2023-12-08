from material import MaterialSpec
from recipe import Recipe


class Machine:
    # TODO: deprecate
    input_producers: dict["Machine", str]
    output_consumers: dict["Machine", str]

    power_consumption: float = 0
    power_production: float = 0

    def __init__(self, recipe: Recipe):
        self.input_producers = {}
        self.output_consumers = {}
        self.recipe = recipe
        self.power_consumption += recipe.variable_power_modifier

    def __str__(self):
        return f"<{self.__class__.__name__}: {self.recipe}>"

    def __repr__(self):
        return str(self)

    def __rshift__(self, material_spec: MaterialSpec):
        """
        Solve for inputs
        Recipe >> MaterialSpec
        """
        # TODO: what should the inverse of div be?
        scale = max(getattr(material_spec, name) / value for name, value in self.recipe.products if value > 0)
        scaled = self.recipe * scale
        return material_spec - scaled

    def __lshift__(self, material_spec: MaterialSpec):
        """
        Solve for outputs
        Recipe << MaterialSpec
        """
        scale = material_spec / self.recipe
        scaled = self.recipe * scale
        return material_spec + scaled

    def __rrshift__(self, material_spec: MaterialSpec):
        """
        Solve for inputs
        MaterialSpec << Recipe
        """
        return self << material_spec

    def __rlshift__(self, material_spec: MaterialSpec):
        """
        Solve for outputs
        MaterialSpec >> Recipe
        """
        return self >> material_spec

    def has_input(self, material: str):
        return getattr(self.recipe.ingredients, material) > 0

    def has_output(self, material: str):
        return getattr(self.recipe.products, material) > 0

    # TODO: there's some serious confusion of responsibilities between this and recipe
    def products(self):
        return [product for product, value in self.recipe.products if value > 0]

    def ingredients(self):
        return [ingredient for ingredient, value in self.recipe.ingredients if value > 0]

    def bind(self, other: "Machine", material: str):
        """
        Verify that there is a matching input-output pair for these two machines

        # TODO: can only handle binding one output to a given machine
        """
        if self.has_output(material) and other.has_input(material):
            other.input_producers[self] = material
            self.output_consumers[other] = material
        elif self.has_input(material) and other.has_output(material):
            self.input_producers[other] = material
            other.output_consumers[self] = material

        return self

    @staticmethod
    def autobind(machines: list["Self"]):
        for i, machine in enumerate(machines):
            for other_machine in machines[i:]:
                for ingredient in machine.ingredients():
                    if other_machine.has_output(ingredient):
                        machine.bind(other_machine, ingredient)
                for product in machine.products():
                    if other_machine.has_input(product):
                        machine.bind(other_machine, product)

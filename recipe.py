from material import MaterialSpec


class Recipe:
    """
    Materials scaled to materials/min
    """

    name: str
    duration: float
    variable_power_modifier: float

    # TODO
    power_consumption: float = 0
    power_production: float = 0

    # TODO
    machine_type: str

    def __init__(self, name: str, ingredients: MaterialSpec, products: MaterialSpec, duration: float, power_modifier: float = 0):
        # FIXME: add div to MaterialSpec
        self.ingredients = ingredients * (1 / duration)
        self.products = products * (1 / duration)
        self.name = name
        self.variable_power_modifier = power_modifier
        self.duration = duration

    def __add__(self, material_spec: MaterialSpec):
        return material_spec + self.products - self.ingredients

    def __radd__(self, material_spec: MaterialSpec):
        return self + material_spec

    def __rsub__(self, material_spec: MaterialSpec):
        return material_spec + self.ingredients - self.products

    def __mul__(self, scalar: float):
        """
        Scale up this recipe
        """
        return type(self)(self.name, self.ingredients * scalar, self.products * scalar)

    def __rtruediv__(self, material_spec: MaterialSpec):
        """
        Get the number of iterations of this recipe that can be produced from the given material_spec
        """
        return min(getattr(material_spec, name) / value for name, value in self.ingredients if value > 0)

    def __repr__(self):
        ingredients = " ".join(repr(self.ingredients).splitlines())
        products = " ".join(repr(self.products).splitlines())

        return f"{ingredients} >> {products}"

    def __rshift__(self, material_spec: MaterialSpec) -> MaterialSpec:
        """
        Solve for inputs
        Recipe >> MaterialSpec
        """
        # TODO: what should the inverse of div be?
        scale = max(getattr(material_spec, name) / value for name, value in self.products if value > 0)
        scaled = self * scale
        return material_spec - scaled

    def __lshift__(self, material_spec: MaterialSpec) -> MaterialSpec:
        """
        Solve for outputs
        Recipe << MaterialSpec
        """
        scale = material_spec / self
        scaled = self * scale
        return material_spec + scaled

    def has_input(self, material: str) -> bool:
        return getattr(self.ingredients, material) > 0

    def has_output(self, material: str) -> bool:
        return getattr(self.products, material) > 0

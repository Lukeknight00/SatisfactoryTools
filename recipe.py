class Recipe:
    name: str
    duration: float

    def __init__(self, name: str, ingredients: MaterialSpec, products: MaterialSpec):
        self.ingredients = ingredients
        self.products = products
        self.name = name

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



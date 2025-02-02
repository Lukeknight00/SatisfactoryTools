import re
from dataclasses import dataclass

from config_parsing.standardization import ConfigData, get_class_name

RECIPE_KEY = "FGRecipe"

# TODO: accelerator recipes have mVariablePowerConsumptionConstant and mVariablePowerConsumptionFactor
# TODO: to account for power difference in recipes

@dataclass
class RecipeData(ConfigData):
    inputs: dict[str, float] 
    outputs: dict[str, float]
    duration: float
    machines: set[str]
    # TODO: power modifiers


def parse_recipes(simple_config: dict[str, ...]) -> list[RecipeData]:
    resource_capture_group = r".*\.(\w+).*?"
    ingredients_pattern = rf"\(ItemClass={resource_capture_group},Amount=(\d+)\)"
    recipes = []

    for config in simple_config[RECIPE_KEY].values():
        recipe_name = config["mDisplayName"]

        ingredients = {name: float(amt) for name, amt in re.findall(ingredients_pattern, config["mIngredients"])}
        products = {name: float(amt) for name, amt in re.findall(ingredients_pattern, config["mProduct"])}

        duration = float(config["mManufactoringDuration"]) / 60  # seconds to minutes
        machines = set(get_class_name(machine) for machine in config["mProducedIn"].strip("()").split(","))

        recipes.append(RecipeData(
            display_name=config["mDisplayName"],
            class_name=config.get("mClassName") or config["ClassName"],
            inputs=ingredients,
            outputs=products,
            machines=machines,
            duration=duration))

    return recipes


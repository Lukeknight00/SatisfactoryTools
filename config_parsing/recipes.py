from typing import re

from config_parsing.standardization import standardize
from recipe import Recipe

RECIPE_KEY = "Class'/Script/FactoryGame.FGRecipe'"

# FIXME: repeated
EXTRACTOR_KEYS = [
    "Class'/Script/FactoryGame.FGBuildableResourceExtractor'",
    "Class'/Script/FactoryGame.FGBuildableWaterPump'"
]

GENERATOR_KEYS = [
    "Class'/Script/FactoryGame.FGBuildableGeneratorFuel'",
    "Class'/Script/FactoryGame.FGBuildableGeneratorNuclear'",
    "Class'/Script/FactoryGame.FGBuildableGeneratorGeoThermal'"
]

# TODO: extractors and generators have 'recipes' bound to the machines
# TODO: accelerator recipes have mVariablePowerConsumptionConstant and mVariablePowerConsumptionFactor
# TODO: to account for power difference in recipes

# TODO: generators have fuels types that have an energy value--just determines burn time, power output
# TODO: isn't variable based on fuel

def make_recipes(simple_config: dict, machine_mapping: dict[str, Machine], material_mapping: dict[str, str]) -> list:
    resource_capture_group = r".*?\.(\w+).*?"
    ingredients_pattern = rf"\(ItemClass={resource_capture_group},Amount=(\d+)\)"
    machines_pattern = fr"({'|'.join(re.escape(m) for m in machine_mapping.keys())})"

    recipes = {}
    tags = {}

    normal_recipes = _parse_normal_recipes()
    extractor_recipes = _parse_extractor_recipes()
    generator_recipes = _parse_generator_recipes()
    # tags: core, alternate, extractor, mk*
    # TODO: put `made in` as key on recipe



    # TODO: extractors and generators have recipe information distrubuted across the machine and
    # TODO: to fuel resources. menergyvalue is MJ, MJ -> c * W*h gives fuel duration and rate

    return machines

def _parse_normal_recipes(simple_config: dict, material_mapping):
    resource_capture_group = r".*?\.(\w+).*?"
    ingredients_pattern = rf"\(ItemClass={resource_capture_group},Amount=(\d+)\)"

    for config in simple_config[RECIPE_KEY].values():
        machine = re.search(machines_pattern, config["mProducedIn"])

        if machine is None:
            continue

        machine = machine_mapping[machine[0]]

        try:
            # FIXME: this metadata dict has approximately 4 different definitions
            recipe_name = standardize(config["mDisplayName"])
            ingredients = {material_mapping[name]: float(amt) / 1000 if material_mapping["material_type"] in ["RF_LIQUID",
                                                                                                              "RF_GAS"] else float(
                amt) for name, amt in re.findall(ingredients_pattern, config["mIngredients"])}
            products = {material_mapping[name]: float(amt) / 1000 if material_mapping["material_type"] in [
                "RF_LIQUID",
                "RF_GAS"] else float(
                amt) for name, amt in re.findall(ingredients_pattern, config["mProduct"])}

            duration = 60 / float(config["mManufactoringDuration"])

            if "alternate" in config["FullName"].lower():
                tags["alternate"].add(recipe_name)
            else:
                tags["core"].add(recipe_name)

            # TODO: use parsed material class
            recipes[recipe_name] = Recipe(recipe_name, MaterialSpec(**ingredients),
                                          MaterialSpec(**products), duration=duration)

        except Exception as e:
            print(f"missing: {e}")
            print()

def _parse_extractor_recipes():
    pass

def _parse_generator_recipes():
    # list of recipes in mFuel, fuel is mFuelClass, additional resource is mSupplementalResourceClass
    # byproduct in mByProduct, amount in mByProductAmount
    # fuel amount and byproducts are on root config, mFuelLoadAmount and mSupplementalLoadAmount
    # TODO: the resource may be a resource category
    for generator in ...:
        fuel_load = generator["mFuelLoadAmount"]
        supplemental_load = generator["mSupplementalLoadAmount"]
        power_output = generator["mPowerProduction"]

        for recipe in generator["mFuel"]:
            # TODO:
            if is_category:
                for fuel_type in category:
                    ...
            fuel = recipe["mFuelClass"]
            supplement = recipe["mSupplementalResourceClass"]
            byproduct = recipe["mByProduct"]
            byproduct_amount = recipe["mByProductAmount"]

            # FIXME: this likely needs a time scale
            rate = material_mapping[fuel]["energy_amount"] / power_output
    pass

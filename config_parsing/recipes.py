from copy import copy
from dataclasses import dataclass
from typing import re

from categorized_collection import CategorizedCollection
from config_parsing.machines import _values_for_key_list
from config_parsing.standardization import standardize
from recipe import Recipe

RECIPE_KEY = "Class'/Script/FactoryGame.FGRecipe'"

# FIXME: repeated
EXTRACTOR_KEYS = [
    "FGBuildableResourceExtractor",
    "FGBuildableWaterPump"
]

GENERATOR_KEYS = [
    "FGBuildableGeneratorFuel",
    "FGBuildableGeneratorNuclear",
    "FGBuildableGeneratorGeoThermal"
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

    recipes = CategorizedCollection()

    recipes.update(_parse_normal_recipes())
    recipes.update(extractor_recipes = _parse_extractor_recipes())
    recipes.update(generator_recipes = _parse_generator_recipes())
    # tags: core, alternate, extractor, mk*
    # TODO: put `made in` as key on recipe

    # TODO: extractors and generators have recipe information distrubuted across the machine and
    # TODO: to fuel resources. menergyvalue is MJ, MJ -> c * W*h gives fuel duration and rate

    return recipes

def _parse_normal_recipes(simple_config: dict, material_mapping):
    resource_capture_group = r".*?\.(\w+).*?"
    ingredients_pattern = rf"\(ItemClass={resource_capture_group},Amount=(\d+)\)"
    recipes = CategorizedCollection()

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
                recipes.add_tag(recipe_name, "alternate")
            else:
                recipes.add_tag(recipe_name, "core")

            # TODO: use parsed material class
            recipes[recipe_name] = Recipe(recipe_name, Materials(**ingredients),
                                          Materials(**products), duration=duration)

        except Exception as e:
            print(f"missing: {e}")
            print()


def _parse_extractor_recipes():
    recipes = CategorizedCollection()

    def get_production_rate(config):
        return (60 / float(config["mExtractCycleTime"])) * float(config["mItemsPerCycle"])

    # FIXME: I think this qualifies as a mess
    for key in EXTRACTOR_KEYS:
        for extractor in simple_config[key].values():
            if "RF_SOLID" in extractor["mAllowedResourceForms"]:
                for material in map(lambda x: standardize(material_config[x]["mDisplayName"]),
                                    simple_config["Class'/Script/FactoryGame.FGResourceDescriptor'"].keys()):
                    recipe = Recipe(material, MaterialSpec(), MaterialSpec(
                        **{material: get_production_rate(extractor)}))
            elif "RF_LIQUID" in extractor["mAllowedResourceForms"] or "RF_GAS" in extractor["mAllowedResourceForms"]:
                for material in map(
                        lambda x: standardize(material_config[re.search(resource_capture_group, x)[1]]["mDisplayName"]),
                        extractor["mAllowedResources"].strip("()").split(",")):
                    machines.fluid_extractors.append(Extractor(Recipe(material, MaterialSpec(), MaterialSpec(
                        **{material: get_production_rate(extractor) / 1000}))))

    return recipes


def _parse_generator_recipes(simple_config, material_mapping, material_class):
    # list of recipes in mFuel, fuel is mFuelClass, additional resource is mSupplementalResourceClass
    # byproduct in mByProduct, amount in mByProductAmount
    # fuel amount and byproducts are on root config, mFuelLoadAmount and mSupplementalLoadAmount
    def _make_recipe(recipe_config, generator):
        fuel = recipe["mFuelClass"]
        supplement = recipe["mSupplementalResourceClass"]
        by_product = recipe["mByProduct"]
        by_product_amount = recipe["mByProductAmount"]

        # TODO: translate material names
        fuel_load = generator["mFuelLoadAmount"]
        supplemental_load = generator["mSupplementalLoadAmount"]
        power_output = generator["mPowerProduction"]

        rate = 60 * material_mapping[fuel].energy_amount / power_output
        ingredients = {fuel: fuel_load}
        if supplement != "":
            ingredients[supplement] = supplemental_load
        products = {}
        if by_product != "":
            products[by_product] = by_product_amount

        return Recipe(material_class(**ingredients), material_class(**products)) * rate

    recipes = CategorizedCollection()

    # FIXME: _values_for_key_list is in a bad spot for importing
    for generator in _values_for_key_list(GENERATOR_KEYS):
        for recipe in generator["mFuel"]:
            if recipe["mFuelClass"] in simple_config:
                recipe = copy(recipe)
                for fuel_type in simple_config[recipe["mFuelClass"]]:
                    recipe["mFuelClass"] = fuel_type["ClassName"]
                    recipes[] = _make_recipe(recipe, generator)

            recipes[] = _make_recipe(recipe)

    return recipes

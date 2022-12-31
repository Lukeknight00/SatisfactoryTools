from copy import copy
import re

from categorized_collection import CategorizedCollection
from config_parsing.machines import _values_for_key_list
from config_parsing.materials import MaterialType, get_material_metadata
from config_parsing.standardization import standardize, get_class_name
from machine import Machine
from material import MaterialSpec
from recipe import Recipe

RECIPE_KEY = "FGRecipe"

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


def parse_recipes(simple_config: dict, machine_mapping: dict[str, Machine], material_mapping: dict[str, str]) -> list:
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


def _parse_normal_recipes(simple_config: dict, materials_class: type[MaterialSpec]):
    resource_capture_group = r".*?\.(\w+).*?"
    ingredients_pattern = rf"\(ItemClass={resource_capture_group},Amount=(\d+)\)"
    recipes = CategorizedCollection()

    material_mapping = {m.internal_name: m for m in get_material_metadata(materials_class)}

    def material_scale(material_internal_name):
        material_type = material_mapping[material_internal_name].material_type
        return .001 if material_type in [MaterialType.LIQUID.value, MaterialType.GAS.value] else 1

    for config in simple_config[RECIPE_KEY].values():
        recipe_name = standardize(config["mDisplayName"])

        try:
            ingredients = [(name, amt) for name, amt in re.findall(ingredients_pattern, config["mIngredients"])]
            ingredients = {material_mapping[name].friendly_name: float(amt) * material_scale(name)
                           for name, amt in ingredients}

            products = [(name, amt) for name, amt in re.findall(ingredients_pattern, config["mProduct"])]
            products = {material_mapping[name].friendly_name: float(amt) * material_scale(name)
                        for name, amt in products}
        except KeyError:
            # we don't have the resources in the material_mapping--usually indicates a non-automated
            # recipe. TODO: have a better detection mechanism for this
            continue

        duration = float(config["mManufactoringDuration"]) / 60  # seconds to minutes

        recipes[recipe_name] = Recipe(recipe_name, materials_class(**ingredients),
                                      materials_class(**products), duration=duration)

        for machine in  config["mProducedIn"].strip("()").split(","):
            recipes.set_tag(recipe_name, get_class_name(machine))

        if "alternate" in config["FullName"].lower():
            recipes.set_tag(recipe_name, "alternate")
        else:
            recipes.set_tag(recipe_name, "core")

    return recipes


def _parse_extractor_recipes(simple_config: dict, materials_class: type[MaterialSpec]):
    recipes = CategorizedCollection()
    material_mapping = {m.internal_name: m for m in get_material_metadata(materials_class)}

    particle_map_pattern = r"\(ResourceNode.*?=.*?\.(\w+),ParticleSystem.*?\)"

    # TODO: tag with mk*

    for key in EXTRACTOR_KEYS:
        for extractor in simple_config[key].values():
            scale = 1 if MaterialType.SOLID.value in extractor["mAllowedResourceForms"] else .001
            items_per_cycle = float(extractor["mItemsPerCycle"]) * scale
            duration = 60 / float(extractor["mExtractCycleTime"])

            if extractor["mAllowedResources"] != "":
                resources = map(get_class_name, extractor["mAllowedResources"].strip("()").split(","))
            else:
                resources = re.findall(particle_map_pattern, extractor["mParticleMap"])

            for resource in resources:
                resource = material_mapping[resource].friendly_name
                recipe = Recipe(resource, materials_class(),
                                materials_class(**{resource: items_per_cycle}),
                                duration=duration)
                recipes[resource] = recipe
                recipes.set_tag(resource, "extractor")

    return recipes


def _parse_generator_recipes(simple_config, materials_class):
    # list of recipes in mFuel, fuel is mFuelClass, additional resource is mSupplementalResourceClass
    # byproduct in mByProduct, amount in mByProductAmount
    # fuel amount and byproducts are on root config, mFuelLoadAmount and mSupplementalLoadAmount

    material_mapping = {m.internal_name: m for m in get_material_metadata(materials_class)}

    def _make_recipe(recipe, generator):
        fuel = material_mapping[recipe["mFuelClass"]]
        supplement = material_mapping.get(recipe["mSupplementalResourceClass"])
        by_product = material_mapping.get(recipe["mByproduct"])

        fuel_load = float(generator["mFuelLoadAmount"])
        power_output = float(generator["mPowerProduction"])

        if fuel.energy_value == 0:
            return None

        duration = (fuel.energy_value / power_output) / 60
        ingredients = {fuel.friendly_name: fuel_load}

        if supplement is not None:
            supplemental_load = float(generator["mSupplementalLoadAmount"])
            ingredients[supplement.friendly_name] = supplemental_load

        products = {}
        if by_product is not None:
            by_product_amount = float(recipe["mByproductAmount"])
            products[by_product.friendly_name] = by_product_amount

        return Recipe(f"{fuel.friendly_name}_power", materials_class(**ingredients),
                      materials_class(**products), duration=duration)

    recipes = CategorizedCollection()

    # FIXME: _values_for_key_list is in a bad spot for importing
    for generator in _values_for_key_list(simple_config, GENERATOR_KEYS):
        generator_name = standardize(generator["mDisplayName"])

        if "mFuel" not in generator:
            # geothermal generator
            continue

        for recipe in generator["mFuel"]:
            if recipe["mFuelClass"] in simple_config:
                recipe = copy(recipe)
                for fuel_type in simple_config[recipe["mFuelClass"]]:
                    fuel_name = material_mapping[fuel_type].friendly_name
                    recipe["mFuelClass"] = material_mapping[fuel_type].internal_name

                    if power_recipe := _make_recipe(recipe, generator) is not None:
                        recipes[f"{generator_name}_{fuel_name}"] = power_recipe

            fuel_name = material_mapping[recipe["mFuelClass"]].friendly_name

            if power_recipe := _make_recipe(recipe, generator) is not None:
                recipes[f"{generator_name}_{fuel_name}"] = power_recipe

    return recipes

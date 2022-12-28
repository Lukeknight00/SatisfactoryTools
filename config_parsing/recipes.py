from typing import re

from config_parsing.standardization import standardize
from recipe import Recipe

RECIPE_KEY = "Class'/Script/FactoryGame.FGRecipe'"


def make_recipes(simple_config: dict, machine_mapping: dict[str, Machine], material_mapping: dict[str, str]) -> list:
    resource_capture_group = r".*?\.(\w+).*?"
    ingredients_pattern = rf"\(ItemClass={resource_capture_group},Amount=(\d+)\)"
    machines_pattern = fr"({'|'.join(re.escape(m) for m in machine_mapping.keys())})"

    recipes = {}
    tags = {}
    # tags: core, alternate, extractor, mk*
    # TODO: put `made in` as key on recipe


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

    # TODO: extractors and generators have recipe information distrubuted across the machine and
    # TODO: to fuel resources. menergyvalue is MJ, MJ -> c * W*h gives fuel duration and rate

    return machines

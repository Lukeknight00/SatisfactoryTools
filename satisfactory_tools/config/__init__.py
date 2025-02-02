import json
import re
from dataclasses import dataclass, make_dataclass, field

from categorized_collection import CategorizedCollection
from config_parsing.machines import MachineData, parse_machines
from config_parsing.materials import parse_materials
from config_parsing.recipes import RecipeData, parse_recipes
from core.material import MaterialSpec
from core.process import ProcessNode


def simplify_config(game_config: list[dict[..., ...]]) -> dict[str, ...]:
    simple_config = {}
    native_class_pattern = r".*\.(\w+)'?"

    for config in game_config:
        if not (match := re.match(native_class_pattern, config["NativeClass"])):
            continue

        key = match.group(1)

        simple_config[key] = {item["ClassName"]: item for item in config["Classes"]}

    return simple_config


@dataclass
class Config:
    recipes: CategorizedCollection[str, ProcessNode]
    materials: MaterialSpec


def parse_config(config_path: str, encoding="utf-16"):
    with open(config_path, "r", encoding=encoding) as f:
        config_data = simplify_config(json.loads(f.read()))
        materials = parse_materials(config_data)
        machines = parse_machines(config_data)
        recipes = parse_recipes(config_data)

        # TODO: pydantic class to have aliases
        materials = make_dataclass("Materials",
                                   [(material.display_name, float, field(default=0)) for material in materials],
                                   bases=(MaterialSpec,), frozen=True)

    return Config(materials=materials, recipes=recipes)


def _make_recipe_data(recipes: CategorizedCollection, machines: dict) -> CategorizedCollection:
    """
    expects recipes to be tagged with the machine keys that they can be constructed by.
    """
    recipe_data = CategorizedCollection()
     # TODO: there are some shortcomings with this CategorizedCollection and managing tags

    for machine_name, machine_type in machines.items():
        for recipe_name, recipe in recipes.tag(machine_name).items():
            recipe_data[recipe_name] = RecipeData(machine=machine_type, recipe=recipe)
            for tag in recipes.value_tags(recipe_name):
                recipe_data.set_tag(recipe_name, tag)

    return recipe_data


def _make_process_node(recipe: RecipeData, machines: list[MachineData]):
    ...

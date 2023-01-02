import json
import re
from dataclasses import dataclass

from categorized_collection import CategorizedCollection
from config_parsing.machines import parse_machines
from config_parsing.materials import parse_materials
from config_parsing.recipes import parse_recipes


def simplify_config(game_config: dict) -> dict:
    simple_config = {}
    native_class_pattern = r".*\.(\w+)'?"
    for config in game_config:
        key = re.match(native_class_pattern, config["NativeClass"]).group(1)
        simple_config[key] = {item["ClassName"]: item for item in config["Classes"]}
    return simple_config


@dataclass
class Config:
    machines: CategorizedCollection
    recipes: CategorizedCollection
    materials: CategorizedCollection


def parse_config(config_path: str, encoding="utf-16"):
    with open(config_path, "r", encoding=encoding) as f:
        config_data = simplify_config(json.loads(f.read()))
        materials = parse_materials(config_data)
        machines = parse_machines(config_data)
        recipes = parse_recipes(config_data, materials)

    return Config(machines=machines, materials=materials, recipes=recipes)


def make_machines(config: Config):
    machines = []

    for machine_name, machine_type in config.machines.items():
        for recipe in config.recipes.tag(machine_name).values():
            machines.append(machine_type(recipe))

    return machines

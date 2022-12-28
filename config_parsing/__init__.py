import json
from dataclasses import dataclass

from categorized_collection import CategorizedCollection


def simplify_config(game_config: dict) -> dict:
    simple_config = {}
    for config in game_config:
        simple_config[config["NativeClass"]] = {item["ClassName"]: item for item in config["Classes"]}
    return simple_config


@dataclass
class Config:
    machines: CategorizedCollection
    recipes: CategorizedCollection
    materials: CategorizedCollection


def parse_config(config_path: str):
    with open(config_path, "r") as f:
        config_data = simplify_config(json.loads(f.read()))
        materials = parse_materials(config_data)
        machines = parse_machines(config_data)
        recipes = parse_recipes(config_data)

    return Config(machines=machines, materials=materials, recipes=recipes)

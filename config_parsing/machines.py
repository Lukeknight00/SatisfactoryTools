import itertools

from categorized_collection import CategorizedCollection
from config_parsing.standardization import standardize
from machine import Machine

BUILDABLE_KEYS = [
    # assembler, constructor, blender, oilrefinery, foundry, smelter, manufacturer
    "FGBuildableManufacturer",
    # collider
    "FGBuildableManufacturerVariablePower",
]

EXTRACTOR_KEYS = [
    "FGBuildableResourceExtractor",
    "FGBuildableWaterPump"
]

GENERATOR_KEYS = [
    "FGBuildableGeneratorFuel",
    "FGBuildableGeneratorNuclear",
    "FGBuildableGeneratorGeoThermal"
]


def _values_for_key_list(simple_config: dict, key_list: list):
    yield from itertools.chain.from_iterable(simple_config[key].values() for key in key_list)


def parse_machines(simple_config: dict) -> CategorizedCollection:
    machines = CategorizedCollection()

    for machine in _values_for_key_list(simple_config, BUILDABLE_KEYS + EXTRACTOR_KEYS + GENERATOR_KEYS):
        power_consumption = machine["mPowerConsumption"]
        name = standardize(machine["mDisplayName"])
        key = machine["ClassName"]
        machine_type = type(name, (Machine,), {"power_consumption": power_consumption})
        machines[key] = machine_type

    return machines


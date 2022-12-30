import itertools
from dataclasses import make_dataclass, field, fields, dataclass
from enum import Enum, auto
from typing import Type

from config_parsing.standardization import standardize
from material import MaterialSpec

RESOURCE_KEYS = ("FGItemDescriptor",
                 "FGResourceDescriptor",
                 "FGConsumableDescriptor",
                 "FGItemDescriptorBiomass",
                 "FGAmmoTypeProjectile",
                 "FGItemDescriptorNuclearFuel",
                 "FGAmmoTypeInstantHit",
                 "FGAmmoTypeSpreadshot")

class MaterialType(Enum):
    SOLID = auto()
    FLUID = auto()


@dataclass
class MaterialMetadata:
    original_name: str
    material_type: MaterialType
    energy_value: float


def get_material_metadata(material_spec: Type["Materials"]) -> dict[str, MaterialMetadata]:
    material_config = {}

    for field in fields(material_spec):
        material_config[field.name] = field.metadata[__file__]

    return material_config


def parse_materials(simple_config: dict) -> Type["Materials"]:
    fields = []
    for internal_name, item in itertools.chain.from_iterable((simple_config[key].items() for key in RESOURCE_KEYS)):
        name = standardize(item["mDisplayName"])
        material_type = MaterialType.SOLID if "solid" in item["mForm"].lower() else MaterialType.FLUID
        metadata = MaterialMetadata(internal_name=internal_name, material_type=material_type, energy_value=float(item["mEnergyValue"]))
        fields.append((name,
                       float,
                       field(default=0,
                             metadata={__file__: metadata})))
    return make_dataclass("Materials", fields, bases=(MaterialSpec,), repr=False)

import itertools
from dataclasses import make_dataclass, field, fields
from typing import Type

from config_parsing.standardization import standardize
from material import MaterialSpec

RESOURCE_KEYS = ("Class'/Script/FactoryGame.FGItemDescriptor'",
                 "Class'/Script/FactoryGame.FGResourceDescriptor'",
                 "Class'/Script/FactoryGame.FGConsumableDescriptor'",
                 "Class'/Script/FactoryGame.FGItemDescriptorBiomass'",
                 "Class'/Script/FactoryGame.FGAmmoTypeProjectile'",
                 "Class'/Script/FactoryGame.FGItemDescriptorNuclearFuel'",
                 "Class'/Script/FactoryGame.FGAmmoTypeInstantHit'",
                 "Class'/Script/FactoryGame.FGAmmoTypeSpreadshot'")


def get_material_metadata(material_spec: Type["Materials"]):
    material_config = {}

    for field in fields(material_spec):
        if "internal_name" in field.metadata:
            material_config[field.metadata["internal_name"]] = field.name

    return material_config


def parse_materials(simple_config: dict) -> Type["Materials"]:
    fields = []
    for internal_name, item in itertools.chain.from_iterable((simple_config[key].items() for key in RESOURCE_KEYS)):
        name = standardize(item["mDisplayName"])
        fields.append((name,
                       float,
                       field(default=0,
                             metadata={"internal_name": internal_name,
                                       "material_type": ...,
                                       "energy_value": ...})))
    # TODO:
    return make_dataclass("Materials", fields, bases=(MaterialSpec,), repr=False)

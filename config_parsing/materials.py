import itertools
from dataclasses import make_dataclass
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


def parse_materials(simple_config: dict) -> Type[MaterialSpec]:
    materials = []
    for item in itertools.chain.from_iterable((simple_config[key].values() for key in RESOURCE_KEYS)):
        materials.append(standardize(item["mDisplayName"]))

    return make_dataclass("Materials", [(mat, float, 0) for mat in materials], bases=(MaterialSpec,), repr=False)

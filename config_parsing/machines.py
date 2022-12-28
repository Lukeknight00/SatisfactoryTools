# TODO: resource wells
"Class'/Script/FactoryGame.FGBuildableFrackingExtractor'" # oil extractor
import itertools

from categorized_collection import CategorizedCollection

"Class'/Script/FactoryGame.FGBuildableFrackingActivator'" # resource well pressurizer

# TODO: geothermal generation--need to work with avg?--variability over time kinda screws with optimization
# TODO: pre-bundle with storage?
"Class'/Script/FactoryGame.FGBuildableGeneratorGeoThermal'"

BUILDABLE_KEYS = [
    # assembler, constructor, blender, oilrefinery, foundry, smelter, manufacturer
    "Class'/Script/FactoryGame.FGBuildableManufacturer'",
    # collider
    "Class'/Script/FactoryGame.FGBuildableManufacturerVariablePower'",
]

EXTRACTOR_KEYS = [
    "Class'/Script/FactoryGame.FGBuildableResourceExtractor'",
    "Class'/Script/FactoryGame.FGBuildableWaterPump'"
]

GENERATOR_KEYS = [
    "Class'/Script/FactoryGame.FGBuildableGeneratorFuel'",
    "Class'/Script/FactoryGame.FGBuildableGeneratorNuclear'"
]

def _values_for_key_list(simple_config: dict, key_list: list):
    yield from itertools.chain.from_iterable(simple_config[key].values() for key in key_list):

"""

    def get_production_rate(config):
        return (60 / float(config["mExtractCycleTime"])) * float(config["mItemsPerCycle"])

    # FIXME: I think this qualifies as a mess
    for key in EXTRACTOR_KEYS:
        for extractor in simple_config[key].values():
            if "RF_SOLID" in extractor["mAllowedResourceForms"]:
                for material in map(lambda x: standardize(material_config[x]["mDisplayName"]),
                                    simple_config["Class'/Script/FactoryGame.FGResourceDescriptor'"].keys()):
                    if "mk1" in extractor["ClassName"].lower():
                        machines.extractors_mk1.append(Extractor(Recipe(material, MaterialSpec(), MaterialSpec(
                            **{material: get_production_rate(extractor)}))))
                    elif "mk2" in extractor["ClassName"].lower():
                        machines.extractors_mk2.append(Extractor(Recipe(material, MaterialSpec(), MaterialSpec(
                            **{material: get_production_rate(extractor)}))))
                    elif "mk3" in extractor["ClassName"].lower():
                        machines.extractors_mk3.append(Extractor(Recipe(material, MaterialSpec(), MaterialSpec(
                            **{material: get_production_rate(extractor)}))))
            elif "RF_LIQUID" in extractor["mAllowedResourceForms"] or "RF_GAS" in extractor["mAllowedResourceForms"]:
                for material in map(
                        lambda x: standardize(material_config[re.search(resource_capture_group, x)[1]]["mDisplayName"]),
                        extractor["mAllowedResources"].strip("()").split(",")):
                    machines.fluid_extractors.append(Extractor(Recipe(material, MaterialSpec(), MaterialSpec(
                        **{material: get_production_rate(extractor) / 1000}))))

"""

def parse_machines(simple_config: dict) -> CategorizedCollection:
    for machine in _values_for_key_list(simple_config, BUILDABLE_KEYS):
        pass

    for machine in _values_for_key_list(simple_config, EXTRACTOR_KEYS):
        # tag both mk* and solid/liquid/gas
        # mAllowedResources is indicator of a fluid extractor
        # mParticleMap is indicator of solid extractor
        pass

    for machine in _values_for_key_list(simple_config, GENERATOR_KEYS):
        if "mVariablePowerProductionCycleFactor" in machine:
            # use average power if powerplant is variable
            pass
        # "mFuel" is key for generator. Can be class of fuel items or fuel items themselves
        # energy values are stored on fuel
        pass
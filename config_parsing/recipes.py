def make_recipes(simple_config: dict, machine_mapping: dict[str, Machine]) -> list:
    resource_capture_group = r".*?\.(\w+).*?"
    ingredients_pattern = rf"\(ItemClass={resource_capture_group},Amount=(\d+)\)"
    machines_pattern = fr"({'|'.join(re.escape(m) for m in machine_mapping.keys())})"
    known_crafters = (
        "Smelter", "Manufacturer", "Assembler", "Packager", "Refinery", "Collider", "Foundry", "Blender", "Constructor")

    machines = Machines()
    material_config = {}
    for key in RESOURCE_KEYS:
        material_config.update(simple_config[key])

    for config in simple_config["Class'/Script/FactoryGame.FGRecipe'"].values():
        machine = re.search(machines_pattern, config["mProducedIn"])

        if machine is None:
            continue

        machine = machine_mapping[machine[0]]

        # TODO: convert resources to friendly names
        try:
            ingredients = {
                standardize(material_config[name]["mDisplayName"]): float(amt) / 1000 if material_config[name][
                                                                                             "mForm"] in ["RF_LIQUID",
                                                                                                          "RF_GAS"] else float(
                    amt) for name, amt in re.findall(ingredients_pattern, config["mIngredients"])}
            products = {standardize(material_config[name]["mDisplayName"]): float(amt) / 1000 if material_config[name][
                                                                                                     "mForm"] in [
                                                                                                     "RF_LIQUID",
                                                                                                     "RF_GAS"] else float(
                amt) for name, amt in re.findall(ingredients_pattern, config["mProduct"])}
            if "alternate" in config["FullName"].lower():
                machines.alternates.append(machine(
                    Recipe(standardize(config["mDisplayName"]), MaterialSpec(**ingredients),
                           MaterialSpec(**products)) * (60 / float(config["mManufactoringDuration"]))))
            else:
                machines.core.append(machine(Recipe(standardize(config["mDisplayName"]), MaterialSpec(**ingredients),
                                                    MaterialSpec(**products)) * (
                                                     60 / float(config["mManufactoringDuration"]))))

        except Exception as e:
            print(f"missing: {e}")
            print()

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

    return machines

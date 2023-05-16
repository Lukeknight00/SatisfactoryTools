from material import MaterialSpec
from process import Process


def total_power(process: Process):
    return sum(p.scale * p.process_root.power_consumption
               for p in filter(lambda p: p.scale > 0,
                               process.process_registry.values()))


def summarize_materials(materials: MaterialSpec):
    pass


def machine_counts(process: Process):
    pass
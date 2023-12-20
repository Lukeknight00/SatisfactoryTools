from dataclasses import field, make_dataclass

from satisfactory_tools.core.material import MaterialSpec

materials = [chr(i) for i in range(97, 107)]

Materials = make_dataclass("Materials",
                           [(name, float, field(default=0)) for name in materials],
                           bases=(MaterialSpec,), frozen=True)


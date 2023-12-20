import plotly.graph_objects as go
from process import Process


def plot_sankey(process: Process):
    ordered_vertices = [m for m in process.process_registry.values() if m.scale > 0]

    edges = [(ordered_vertices.index(process.process_registry[other]), ordered_vertices.index(self)) for self in ordered_vertices for other in self.process_root.input_producers if process.process_registry[other] in ordered_vertices]
    source, target = zip(*edges)

    def get_materials_for_link(start: int, end: int, vertices: list[Process]):
        start_process = vertices[start]
        end_process = vertices[end]
        bound_material = start_process.process_root.output_consumers[end_process.process_root]
        return bound_material, (getattr(end_process.process_root.recipe.ingredients, bound_material) * end_process.scale)

    labels, weights = zip(*[get_materials_for_link(start, end, ordered_vertices) for (start, end) in edges])

    fig = go.Figure()
    fig.add_trace(
        go.Sankey(
            node=dict(
                label = [f"{v.process_root.__class__.__name__}: {v.process_root.recipe.name}" for v in ordered_vertices]
            ),
            link=dict(
                source=source,
                target=target,
                value=weights,
                label=labels
            )
        )
    )
    fig.show()

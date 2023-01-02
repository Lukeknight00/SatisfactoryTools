import itertools
import math
from textwrap import dedent

from process import Process
from igraph import Graph, EdgeSeq
import plotly.graph_objects as go


def make_hover_label(process: Process):
    return dedent(f"""
    {process.process_root.__class__.__name__}<br>
    Recipe: {process.process_root.recipe.name}<br>
    Scale: {process.scale}
    """)


# TODO: show machine types in legend
def plot_process(process: Process, layout=Graph.layout_auto):
    ordered_vertices = [m for m in process.process_registry.values() if m.scale > 0]
    n_vertices = len(ordered_vertices)

    edges = [(ordered_vertices.index(process.process_registry[other]), ordered_vertices.index(self)) for self in ordered_vertices for other in self.process_root.input_producers if process.process_registry[other] in ordered_vertices]

    G = Graph(n_vertices, edges)
    layout = G.layout(layout)
    Xn, Yn = list(zip(*layout))
    edge_coords = itertools.chain.from_iterable([[(Xn[n], Yn[n]) for n in e] + [(None, None)] for e in edges])
    Xe, Ye = list(zip(*edge_coords))

    max_scale = max(n.scale for n in ordered_vertices)
    point_scale = 20
    point_sizes = [(math.tanh(n.scale  / max_scale) + 1) * point_scale for n in ordered_vertices]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=Xe,
        y=Ye,
        mode='lines+markers',
        hoverinfo='none',
        line_shape='spline',
        marker=dict(
            symbol="arrow-wide",
            size=10,
            color="black",
            angleref="previous",
            standoff=point_scale//2
        ),
        showlegend=False
    ),

    )

    fig.add_trace(go.Scatter(x=Xn,
                             y=Yn,
                             mode='markers',
                             marker=dict(symbol='circle-dot',
                                         size=point_sizes,
                                         # color=[m.process_root.color for m in ordered_vertices],
                                         ),
                             text=[make_hover_label(v) for v in ordered_vertices],
                             hovertemplate="%{text}<extra></extra>",
                             showlegend=False,
                             )
                  )

    # TODO: better sizing
    fig.update_layout(
        autosize=True,
        xaxis= {
            'showgrid': False, # thin lines in the background
            'zeroline': False, # thick line at x=0
            'visible': False,  # numbers below
        },
        yaxis= {
            'showgrid': False, # thin lines in the background
            'zeroline': False, # thick line at x=0
            'visible': False,  # numbers below
        },
        height=1000
    )

    fig.show()

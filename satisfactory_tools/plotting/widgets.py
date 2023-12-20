from collections import defaultdict
from dataclasses import asdict
from typing import Mapping, Tuple, Type

from ipytree import Node, Tree
from ipywidgets import Button, dlink, interactive
from material import MaterialSpec
from process import Process

from config_parsing import RecipeData


class TreeSelectionProxy(Mapping[str, RecipeData]):
    def __init__(self, proxied_tree: Tree, proxied_collection: Mapping):
        self._tree = proxied_tree
        self._proxied_collection = proxied_collection
        self._values = {}

    def _update(self):
        self._values = {node.name: self._proxied_collection[node.name]
                        for node in self._tree.selected_nodes
                        if node.name in self._proxied_collection}

    def __getitem__(self, item):
        self._update()
        return self._values[item]

    def values(self):
        self._update()
        yield from self._values.values()

    def keys(self):
        self._update()
        yield from self._values.keys()

    def items(self):
        self._update()
        yield from self._values.items()

    def __iter__(self):
        yield from self.items()

    def __len__(self) -> int:
        self._update()
        return len(self._values)

def recipe_widget(recipes) -> Tuple[Tree, Mapping[str, RecipeData]]:
    tree = Tree(stripes=False)
    nodes = defaultdict(list)

    for tag in recipes.tags:
        tag_node = Node(str(tag), opened=False)
        tree.add_node(tag_node)
        for label in recipes.tag(tag).keys():
            node = Node(str(label), icon="")
            nodes[label].append(node)
            tag_node.add_node(node)

    # dlink avoids an 'event bomb' from these updates creating events for all linked nodes.
    # still slow, just not _as_ slow.
    for label_nodes in nodes.values():
        label_nodes = list(label_nodes)
        for first, second in zip(label_nodes[:-1], label_nodes[1:]):
            dlink((first, "selected"), (second, "selected"))

        if len(label_nodes) >= 2:
            dlink((label_nodes[0], "selected"), (label_nodes[-1], "selected"))

    return tree, TreeSelectionProxy(tree, recipes)


def material_widget(material_class: Type[MaterialSpec], value_range=(-1000, 1000)):
    materials = material_class()
    w = interactive(materials.__init__, **{k: value_range for k in asdict(materials).keys()})
    return w, materials


def optimize_inputs_widget(callback, available, target_output, recipes, generation=False):
    button = Button(description="Optimize from Inputs")

    def optimize(_):
        machines = [r.instance() for r in recipes.values()]
        callback(Process.from_inputs(available, target_output, machines))

    button.on_click(optimize)


def optimize_outputs_widget(callback, target_output, recipes, generation=False):
    button = Button(description="Optimize from Outputs")

    def optimize(_):
        button.button_style = "danger"
        button.disabled = True
        old_text = button.description
        button.description = "Working"
        machines = [r.instance() for r in recipes.values()]

   
        callback(Process.from_outputs(target_output, machines, include_power=generation))

        # finally:
        #     button.button_style = ""
        #     button.description = old_text
        #     button.disabled = False

    button.on_click(optimize)
    return button

from dataclasses import asdict
from typing import Type

from ipywidgets import interactive, Button, jslink
from ipytree import Node, Tree

from material import MaterialSpec
from process import Process


def recipe_widget(recipes):
    tree = Tree(stripes=False)
    nodes = {}
    recipe_subset = {}

    def update_recipes(update):
        new = update["new"]
        old = update["old"]
        for new_selection in new:
            # filter out tag nodes
            if new_selection.name in recipes:
                recipe_subset[new_selection.name] = recipes[new_selection.name]

        for old_selection in old:
            if old_selection not in new:
                del recipe_subset[old_selection.name]

    for tag in recipes.tags:
        tag_node = Node(str(tag), opened=False)
        tree.add_node(tag_node)
        for label in recipes.tag(tag).keys():
            if label in nodes:
                node = Node(str(label), icon="")
                jslink((node, "selected"), (nodes[label], "selected"))
            else:
                node = nodes.setdefault(label, Node(str(label), icon=""))
            tag_node.add_node(node)

    tree.observe(update_recipes, names="selected_nodes")
    return tree, recipe_subset


def material_widget(material_class: Type[MaterialSpec]):
    materials = material_class()
    w = interactive(materials.__init__, **asdict(materials))
    return w, materials


def optimize_inputs_widget(callback, available, target_output, recipes, generation=False):
    button = Button(description="Optimize from Inputs")

    def optimize(_):
        # TODO: figure out how to return output from callback
        machines = [r.instance() for r in recipes.values()]
        callback(Process.from_inputs(available, target_output, machines))

    button.on_click(optimize)


def optimize_outputs_widget(callback, target_output, recipes, generation=False):
    button = Button(description="Optimize from Outputs")

    def optimize(_):
        # TODO: figure out how to return output from callback
        button.button_style = "danger"
        button.disabled = True
        old_text = button.description
        button.description = "Working"
        machines = [r.instance() for r in recipes.values()]

        try:
            callback(Process.from_outputs(target_output, machines, include_power=generation))
        finally:
            button.button_style = ""
            button.description = old_text
            button.disabled = False

    button.on_click(optimize)
    return button

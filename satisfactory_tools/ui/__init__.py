from nicegui import ui
from .widgets import fuzzy_sort_picker
from satisfactory_tools.categorized_collection import CategorizedCollection
import random
import string


# @ui.page('/{process_file}')
# def process(process_file: str):
#     # TODO: failed to open fallback
#     with open(process_file) as f:
#         ...

tags = ["".join(random.choices(string.ascii_letters, k=random.randint(5, 10))) for _ in range(15)]
items = {"".join(random.choices(string.ascii_letters, k=random.randint(5, 10))): i for i in range(200)}
tag_assignments = {tag: set(random.choices(list(items.keys()), k=random.randint(4, 40))) for tag in tags}
test_collection = CategorizedCollection(items, tag_assignments)

ui.dark_mode()

with ui.stepper().props("vertical").classes("w-full") as stepper:
    with ui.step("Target Output"):
        fuzzy_sort_picker(ui, test_collection)
        ui.button("Apply")
    with ui.step("Input Constraints"):
        fuzzy_sort_picker(ui, test_collection)
        with ui.row():
            ui.button("Skip")
            ui.button("Apply")
    with ui.step("Available Recipes"):
        fuzzy_sort_picker(ui, test_collection)
        ui.button("Apply")
    with ui.step("Optimize"):
        with ui.row():
            # TODO: more description
            ui.button("Maximize output")
            ui.button("Minimize input")

ui.run()

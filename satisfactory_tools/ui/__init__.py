from nicegui import ui
from .widgets import fuzzy_sort_picker
from satisfactory_tools.categorized_collection import CategorizedCollection


ui.label("Satisfactory Planning")

# @ui.page('/{process_file}')
# def process(process_file: str):
#     # TODO: failed to open fallback
#     with open(process_file) as f:
#         ...

test_collection = CategorizedCollection()
test_collection["a"] = 1
test_collection["b"] = 2
test_collection["c"] = 3
test_collection["d"] = 4

test_collection.set_tag("a", "letter")
test_collection.set_tag("b", "number")
test_collection.set_tag("c", "animal")
test_collection.set_tag("d", "vegetable")
fuzzy_sort_picker(ui, test_collection)

ui.run()

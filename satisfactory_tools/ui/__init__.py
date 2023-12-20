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
fuzzy_sort_picker(ui, test_collection)

ui.run()

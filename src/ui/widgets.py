from categorized_collection import CategorizedCollection
from thefuzz import process
from nicegui import ui


def material_selection():
    pass

def fuzzy_sort_picker(ui: ui, elements: CategorizedCollection[str, ...]):
    with ui.splitter() as splitter:
        with splitter.before:
            searchbox = ui.input(placeholder="Search...", on_change=lambda e: _fuzzy_filter(e.value, elements))
            searchbox.props("clearable")
            # TODO: categories--use badges to indicate total selected
            # TODO: state flow: unselected -> selected, selected -> unselected, partially selected -> unselected
            # partial selection from filtered view, in which case you go from unselected -> partially selected, or by 
            # selecting checks manually

        with splitter.after:
            with ui.scroll_area(), ui.grid():
                # TODO: filtered elements, not full elements
                for key in elements.keys():
                    ui.switch(key)


def _fuzzy_filter(search: str, search_over: CategorizedCollection[str, ...]) -> CategorizedCollection:
    pass

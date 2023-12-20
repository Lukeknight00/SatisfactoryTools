from satisfactory_tools.categorized_collection import CategorizedCollection
from thefuzz import process
from nicegui import ui
from collections import Counter
from functools import partial


def material_selection():
    pass

class Picker:
    def __init__(self, elements: CategorizedCollection[str, ...]):
        self.elements = elements
        self._visible = {key: True for key in self.elements.keys()}
        self._selected = {key: False for key in self.elements.keys()}

    def _selected_for_category(self, category: str) -> int:
        return sum(self.selected[k] for k in self.elements.tag[category].keys())

    # def _selected

    def render_category_selectors(self, ui: ui) -> None:
        for tag in self.elements.tags.keys():
            with ui.button(tag, on_click=partial(self._category_select, tag)):
                ui.badge(0).bind_text_from(self._categories, tag).props("floating")

    def render_search_box(self, ui: ui) -> None:
        searchbox = ui.input(placeholder="Search...", on_change=lambda e: self._filter(e.value))
        searchbox.props("clearable")

    def render_selectors(self, ui: ui) -> None:
        for key in self.elements.keys():
            switch = ui.switch(key)
            switch.bind_value(self._selected, key)
            switch.bind_visibility_from(self._visible, key)

    def _category_select(self, category: str) -> None:
        for value in set(self.elements.tag(category).keys()) & {k for k, v in self._visible.items() if v}:
            self._selected[value] = True

    def _filter(self, search: str):
        # TODO: also filter category visiblity
        if not search:
            for key in self._visible.keys():
                self._visible[key] = True
            return

        threshold = 75
        scores = process.extract(search, self.elements.keys())
        for k, score in scores:
            self._visible[k] = score

    @property
    def selected(self) -> set[...]:
        yield from (elements[key] for key, value in self._selected.items() if value)



def fuzzy_sort_picker(ui: ui, elements: CategorizedCollection[str, ...]):
    picker = Picker(elements)
    with ui.splitter() as splitter:
        with splitter.before:
            picker.render_search_box(ui)
            # TODO: categories--use badges to indicate total selected
            # TODO: state flow: unselected -> selected, selected -> unselected, partially selected -> unselected
            # partial selection from filtered view, in which case you go from unselected -> partially selected, or by 
            # selecting checks manually
            picker.render_category_selectors(ui)

        with splitter.after:
            with ui.scroll_area(), ui.grid():
                picker.render_selectors(ui)


def _fuzzy_filter(search: str, search_over: CategorizedCollection[str, ...]) -> CategorizedCollection:
    pass

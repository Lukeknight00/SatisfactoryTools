from satisfactory_tools.categorized_collection import CategorizedCollection
from thefuzz import process
from nicegui import ui
from collections import Counter
from functools import partial


class Picker:
    def __init__(self, elements: CategorizedCollection[str, ...]):
        self.elements = elements
        self._selected = {key: False for key in self.elements.keys()}
        self._selector_visibility = {key: True for key in self.elements.keys()}

        self._category_visibility = {key: True for key in self.elements.keys()}
        self._category_counters = {key: 0 for key in self.elements.keys()}

    def render_category_selectors(self, ui: ui) -> None:
        for tag in self.elements.tags.keys():
            with ui.circular_progress(max=len(list(self.elements.tag(tag).values())), show_value=False).bind_value_from(self._category_counters, tag).bind_visibility_from(self._category_visibility, tag):
                ui.button(tag, on_click=partial(self._category_select, tag)).props("flat round").bind_visibility_from(self._category_visibility, tag)


    def render_search_box(self, ui: ui) -> None:
        searchbox = ui.input(placeholder="Search...", on_change=lambda e: self._filter(e.value))
        searchbox.props("clearable")

    def render_selectors(self, ui: ui) -> None:
        for key in self.elements.keys():
            # FIXME: there might be an update order thing here, with a race between updating selected
            # FIXME: and updating the category selectors. The on_change might have the value in an event,
            # FIXME: which would obviate this issue entirely.
            # FIXME: there's also a parallel issue, in that selecting by category will trigger the
            # FIXME: on_change for every element in the category
            switch = ui.switch(key, on_change=partial(self._update_category_selectors, item=key))
            switch.bind_value(self._selected, key)
            switch.bind_visibility_from(self._selector_visibility, key)

    def _category_select(self, category: str) -> None:
        visible_keys = set(self.elements.tag(category).keys()) & {k for k, v in self._selector_visibility.items() if v}
        all_selected = all(self._selected[key] for key in visible_keys)
        for value in visible_keys:
            self._selected[value] = not all_selected

        self._update_category_selectors()

    def _update_category_selectors(self, item: str | None = None):
        print("category update")
        if item:
            update_tags = self.elements.value_tags(item)
        else:
            update_tags = set(self.elements.tags.keys())

        for tag in update_tags:
            self._category_counters[tag] = sum(self._selected[k] for k in self.elements.tag(tag).keys())

    def _filter(self, search: str):
        if not search:
            for key in self._selector_visibility.keys():
                self._selector_visibility[key] = True

            for key in self._category_visibility.keys():
                self._category_visibility[key] = True

            return

        threshold = 75

        item_scores = process.extract(search, self.elements.keys(), limit=None)
        tag_scores = process.extract(search, self.elements.tags.keys(), limit=None)
        visible_categories = {k for k, score in tag_scores if score > threshold}
        for k, score in item_scores:
            self._selector_visibility[k] = (score > threshold) or any(visible_categories & self.elements.value_tags(k))

        for k, score in tag_scores:
            self._category_visibility[k] = (score > threshold)

    @property
    def selected(self) -> set[...]:
        yield from (self.elements[key] for key, value in self._selected.items() if value)



def fuzzy_sort_picker(ui: ui, elements: CategorizedCollection[str, ...]):
    picker = Picker(elements)
    picker.render_search_box(ui)
    # TODO: categories--use badges to indicate total selected
    # TODO: state flow: unselected -> selected, selected -> unselected, partially selected -> unselected
    # partial selection from filtered view, in which case you go from unselected -> partially selected, or by 
    # selecting checks manually
    with ui.row() as grid:
        picker.render_category_selectors(ui)

    with ui.row() as grid:
        picker.render_selectors(ui)


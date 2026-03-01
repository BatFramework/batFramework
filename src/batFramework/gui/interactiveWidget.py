from .widget import Widget
from typing import Self
import pygame
import batFramework as bf


def children_has_focus(widget) -> bool:
    if isinstance(widget, InteractiveWidget) and widget.is_focused:
        return True
    for child in widget.children:
        if children_has_focus(child):
            return True
    return False


class InteractiveWidget(Widget):

    def __init__(self, *args, **kwargs) -> None:
        self.is_focused: bool = False
        self.is_hovered: bool = False
        self.is_clicked_down: list[bool] = [False] * 5
        self.focused_index = 0
        self.is_enabled: bool = True
        self.click_pass_through: bool = False
        super().__init__(*args, **kwargs)

    # -------------------------------------------------------------------------
    # Event dispatch
    # -------------------------------------------------------------------------

    def handle_event(self, event):
        if self.is_hovered:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.is_clicked_down[event.button - 1] = True
                self.on_click_down(event.button, event)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.is_clicked_down[event.button - 1] = False
                self.on_click_up(event.button, event)

        if self.is_focused:
            if event.type == pygame.KEYDOWN:
                self.on_key_down(event.key, event)
            elif event.type == pygame.KEYUP:
                self.on_key_up(event.key, event)

    # -------------------------------------------------------------------------
    # Focus management
    # -------------------------------------------------------------------------

    def set_click_pass_through(self, pass_through: bool) -> Self:
        """Allows mouse click events to pass through this widget to underlying widgets if True."""
        self.click_pass_through = pass_through
        return self

    def allow_focus_to_self(self) -> bool:
        return self.visible and self.is_enabled

    def ask_focus(self, focus_area: pygame.Rect = None) -> bool:
        """Request focus from root widget if self allows focus."""
        if self.allow_focus_to_self() and ((r := self.get_root()) is not None):
            r.focus_on(self, focus_area)
            return True
        return False

    def lose_focus(self) -> bool:
        if self.is_focused and ((r := self.get_root()) is not None):
            r.focus_on(None)
            return True
        return False

    def set_parent(self, parent: Widget) -> Self:
        if parent is None and children_has_focus(self):
            self.get_root().clear_focused()
        return super().set_parent(parent)

    def set_focused_child(self, child: "InteractiveWidget", focus_area: pygame.Rect = None):
        pass

    # -------------------------------------------------------------------------
    # Tab-order navigation helpers
    # -------------------------------------------------------------------------

    def get_interactive_widgets(self):
        """Retrieve all interactive widgets in the tree, in depth-first order."""
        widgets = []
        stack = [self]
        while stack:
            widget = stack.pop()
            if isinstance(widget, InteractiveWidget) and widget.allow_focus_to_self():
                widgets.append(widget)
            stack.extend(reversed(widget.children))
        return widgets

    def find_next_widget(self, current):
        """Find the next interactive widget, considering parent and sibling relationships."""
        if current.is_root:
            return None

        siblings = (
            current.parent.get_interactive_children()
            if hasattr(current.parent, "layout")
            else current.parent.children
        )
        try:
            start_index = siblings.index(current)
        except ValueError:
            start_index = 0

        good_index = -1
        for i in range(start_index + 1, len(siblings)):
            sibling = siblings[i]
            if isinstance(sibling, InteractiveWidget) and sibling is not current:
                if sibling.allow_focus_to_self():
                    good_index = i
                    break

        if good_index >= 0:
            return siblings[good_index]
        return self.find_next_widget(current.parent)

    def find_prev_widget(self, current: "Widget"):
        """Find the previous interactive widget, considering parent and sibling relationships."""
        if current.is_root:
            return None

        siblings = (
            current.parent.get_interactive_children()
            if hasattr(current.parent, "layout")
            else current.parent.children
        )
        try:
            start_index = siblings.index(current)
        except ValueError:
            start_index = 0

        good_index = -1
        for i in range(start_index - 1, -1, -1):
            sibling = siblings[i]
            if isinstance(sibling, InteractiveWidget) and sibling is not current:
                if sibling.allow_focus_to_self():
                    good_index = i
                    break

        if good_index >= 0:
            return siblings[good_index]
        return self.find_prev_widget(current.parent)

    def focus_next_tab(self, previous_widget):
        """Focus the next interactive widget."""
        if previous_widget:
            next_widget = self.find_next_widget(previous_widget)
            if next_widget:
                next_widget.ask_focus()

    def focus_prev_tab(self, previous_widget):
        """Focus the previous interactive widget."""
        if previous_widget:
            prev_widget = self.find_prev_widget(previous_widget)
            if prev_widget:
                prev_widget.ask_focus()

    # -------------------------------------------------------------------------
    # Event handlers — override in subclasses via do_* hooks
    # -------------------------------------------------------------------------

    def on_key_down(self, key, event) -> None:
        self.do_on_key_down(key, event)

    def on_key_up(self, key, event) -> None:
        self.do_on_key_up(key, event)

    def on_click_down(self, button: int, event=None) -> None:
        if not self.click_pass_through:
            event.consumed = True
        self.do_on_click_down(button, event)

    def on_click_up(self, button: int, event=None) -> None:
        if not self.click_pass_through:
            event.consumed = True
        self.do_on_click_up(button, event)

    def on_get_focus(self, focus_area: pygame.Rect = None) -> None:
        self.is_focused = True
        if isinstance(self.parent, bf.gui.InteractiveWidget):
            self.parent.set_focused_child(self, focus_area)
        self.do_on_get_focus()

    def on_lose_focus(self) -> None:
        self.is_focused = False
        self.do_on_lose_focus()

    def on_enter(self) -> None:
        self.is_hovered = True
        self.dirty_surface = True
        self.do_on_enter()

    def on_exit(self) -> None:
        self.is_hovered = False
        self.is_clicked_down = [False] * 5
        self.dirty_surface = True
        self.do_on_exit()

    def on_mouse_motion(self, x, y) -> None:
        self.do_on_mouse_motion(x, y)

    # -------------------------------------------------------------------------
    # do_* extension hooks (override in subclasses)
    # -------------------------------------------------------------------------

    def do_on_get_focus(self) -> None:
        pass

    def do_on_lose_focus(self) -> None:
        pass

    def do_on_key_down(self, key, event) -> None:
        return

    def do_on_key_up(self, key, event) -> None:
        return

    def do_on_click_down(self, button: int, event=None) -> None:
        return

    def do_on_click_up(self, button: int, event=None) -> None:
        return

    def do_on_enter(self) -> None:
        pass

    def do_on_exit(self) -> None:
        pass

    def do_on_mouse_motion(self, x, y) -> None:
        pass

    # -------------------------------------------------------------------------
    # Enable / disable
    # -------------------------------------------------------------------------

    def enable(self) -> Self:
        self.is_enabled = True
        self.dirty_surface = True
        return self

    def disable(self) -> Self:
        self.is_enabled = False
        self.dirty_surface = True
        return self
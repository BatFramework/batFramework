from .widget import Widget
from typing import Callable, Self,Any
import pygame
import batFramework as bf
import logging

logger = logging.getLogger(__name__)

def children_has_focus(widget) -> bool:
    if isinstance(widget, InteractiveWidget) and widget.is_focused:
        return True
    for child in widget.children:
        if children_has_focus(child):
            return True
    return False


class InteractiveWidget(Widget):
    is_focus_scope: bool = False
    trap_focus: bool = False
    def __init__(self, *args, **kwargs) -> None:
        self.is_focused: bool = False
        self.is_hovered: bool = False
        self.is_clicked_down: list[bool] = [False] * 5
        # Physical button state while a mouse press that began here is active.
        # Keep it separate from is_clicked_down, which subclasses also use for
        # keyboard and programmatic clicks.
        self._mouse_pressed_snapshot: list[bool] | None = None
        self.focused_index = 0
        self.is_enabled: bool = True
        self.click_pass_through: bool = False
        self.custom_handlers: dict[pygame.Event, tuple[bool,bool,Callable[[Self], bool]]] = {}
        super().__init__(*args, **kwargs)

    # -------------------------------------------------------------------------
    # Event dispatch
    # -------------------------------------------------------------------------

    def handle_event(self, event):

        if self.is_hovered:
            if (event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP)
                    and 1 <= event.button <= 5):
                pressed = event.type == pygame.MOUSEBUTTONDOWN
                if self.is_clicked_down[event.button - 1] != pressed:
                    self._track_mouse_button(event.button, pressed)
                    self.is_clicked_down[event.button - 1] = pressed
                    if pressed:
                        self.on_click_down(event.button, event)
                    else:
                        self.on_click_up(event.button, event)
                    if not any(self.is_clicked_down):
                        self._mouse_pressed_snapshot = None

        if self.is_focused:
            if event.type == pygame.KEYDOWN:
                self.on_key_down(event.key, event)
            elif event.type == pygame.KEYUP:
                self.on_key_up(event.key, event)

        if event.type in self.custom_handlers:
            if_hovered, if_focused, handler = self.custom_handlers[event.type]
            if (not if_hovered or self.is_hovered) and (not if_focused or self.is_focused):
                if handler(self, event):
                    event.consumed = True
                    return

    def _track_mouse_button(self, button: int, pressed: bool) -> None:
        """Record an event handled here, including presses forwarded by a parent."""
        if self._mouse_pressed_snapshot is None:
            if not pressed:
                return
            self._mouse_pressed_snapshot = list(pygame.mouse.get_pressed(5))
        self._mouse_pressed_snapshot[button - 1] = pressed

    def update(self, dt: float) -> None:
        super().update(dt)
        if self._mouse_pressed_snapshot is None:
            return
        pressed_now = list(pygame.mouse.get_pressed(5))
        for index, (was_pressed, is_pressed) in enumerate(
                zip(self._mouse_pressed_snapshot, pressed_now)):
            if was_pressed == is_pressed:
                continue
            was_owned = self.is_clicked_down[index]
            self.is_clicked_down[index] = is_pressed
            event = pygame.event.Event(
                pygame.MOUSEBUTTONDOWN if is_pressed else pygame.MOUSEBUTTONUP,
                button=index + 1, pos=pygame.mouse.get_pos(), consumed=False,
                synthetic_capture=True,
            )
            if is_pressed:
                self.on_click_down(index + 1, event)
            elif was_owned:
                self.on_click_up(index + 1, event)
        self._mouse_pressed_snapshot = pressed_now if any(self.is_clicked_down) else None


    # -----------------------------------------------------------------
    # Scope discovery and tree descent (generic, not overridden often)
    # -----------------------------------------------------------------

    def find_focus_scope(self) -> "InteractiveWidget | None":
        """Walk up to find the nearest enclosing focus scope."""
        w = self.parent
        while w is not None:
            if isinstance(w, InteractiveWidget) and w.is_focus_scope:
                return w
            w = w.parent
        return None

    def find_first_focusable(self) -> "InteractiveWidget | None":
        if isinstance(self, InteractiveWidget) and self.allow_focus_to_self():
            return self
        for c in self.children:
            if isinstance(c, InteractiveWidget):
                r = c.find_first_focusable()
                if r is not None:
                    return r
        return None

    def find_last_focusable(self) -> "InteractiveWidget | None":
        for c in reversed(self.children):
            if isinstance(c, InteractiveWidget):
                r = c.find_last_focusable()
                if r is not None:
                    return r
        if isinstance(self, InteractiveWidget) and self.allow_focus_to_self():
            return self
        return None

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


    # -----------------------------------------------------------------
    # Scope behavior — defaults that handle the common case.
    # Override `get_next_focus` / `get_prev_focus` / `_focus_candidates`
    # on a subclass for custom navigation.
    # -----------------------------------------------------------------

    def _focus_candidates(self) -> list["Widget"]:
        """Children this scope considers part of its tab order."""
        return list(self.children)

    def get_next_focus(self, from_widget: "InteractiveWidget") -> "InteractiveWidget | None":
        """Called on a scope. Returns the next focus target after `from_widget` within this scope."""
        if not self.is_focus_scope:
            # Non-scopes just delegate up.
            return self.parent.get_next_focus(from_widget) if isinstance(self.parent, InteractiveWidget) else None
        return self._step_focus(from_widget, +1)

    def get_prev_focus(self, from_widget: "InteractiveWidget") -> "InteractiveWidget | None":
        if not self.is_focus_scope:
            return self.parent.get_prev_focus(from_widget) if isinstance(self.parent, InteractiveWidget) else None
        return self._step_focus(from_widget, -1)

    def _step_focus(self, from_widget: "InteractiveWidget", direction: int) -> "InteractiveWidget | None":
        candidates = self._focus_candidates()

        # Find which candidate contains from_widget (could be from_widget itself, or an ancestor of it).
        idx = -1
        for i, c in enumerate(candidates):
            if c is from_widget or self._is_descendant(from_widget, c):
                idx = i
                break

        # Walk in `direction` from idx, looking for next focusable.
        if direction > 0:
            search_range = range(idx + 1, len(candidates))
        else:
            search_range = range(idx - 1, -1, -1)

        for i in search_range:
            target = candidates[i]
            if not isinstance(target, InteractiveWidget):
                continue
            first = target.find_first_focusable() if direction > 0 else target.find_last_focusable()
            if first is not None:
                return first

        # Ran off the end of this scope.
        if self.trap_focus:
            # Wrap within this scope.
            wrap_range = range(0, len(candidates)) if direction > 0 else range(len(candidates) - 1, -1, -1)
            for i in wrap_range:
                target = candidates[i]
                if not isinstance(target, InteractiveWidget):
                    continue
                first = target.find_first_focusable() if direction > 0 else target.find_last_focusable()
                if first is not None and first is not from_widget:
                    return first
            return None

        # Delegate to the next enclosing scope.
        outer = self.find_focus_scope()
        if outer is None:
            return None
        return outer.get_next_focus(self) if direction > 0 else outer.get_prev_focus(self)

    @staticmethod
    def _is_descendant(w: "Widget", ancestor: "Widget") -> bool:
        while w is not None:
            if w is ancestor:
                return True
            w = w.parent
        return False

    # -----------------------------------------------------------------
    # Public entry points
    # -----------------------------------------------------------------

    def focus_next_tab(self, current: "InteractiveWidget" = None) -> None:
        # logger.debug(f"focus next in {self=} {current=}")
        current = current or self
        scope = current.find_focus_scope()
        if scope is None:
            return
        nxt = scope.get_next_focus(current)
        if nxt is not None:
            nxt.ask_focus()

    def focus_prev_tab(self, current: "InteractiveWidget" = None) -> None:
        # logger.debug(f"focus prev in {self=} {current=}")

        current = current or self
        scope = current.find_focus_scope()
        if scope is None:
            return
        prv = scope.get_prev_focus(current)
        if prv is not None:
            prv.ask_focus()

 
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
        if self._mouse_pressed_snapshot is None:
            self.is_clicked_down = [False] * 5
        self.dirty_surface = True
        self.do_on_exit()

    def on_mouse_motion(self, x, y) -> None:
        self.do_on_mouse_motion(x, y)

    def add_custom_handler(
            self, event_type: int, handler: Callable[[Self, pygame.Event], bool], 
            if_hovered: bool = False, if_focused: bool = False) -> Self:
        """Add a custom event handler for a specific Pygame event type. The handler should return True if it consumes the event."""
        self.custom_handlers[event_type] = (if_hovered, if_focused, handler)
        return self

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

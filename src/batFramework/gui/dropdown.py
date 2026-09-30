import dataclasses

import pygame 
import batFramework as bf
from typing import Self, Callable, Any, TypeVar, Generic
from batFramework.gui.interactiveWidget import InteractiveWidget
from .toggle import Toggle
from .indicator import ArrowIndicator
from .clickableWidget import ClickableWidget
from .syncedVar import SyncedVar
from .scrollingContainer import ScrollingContainer
from .layout import Column
from .button import Button

OptionType = TypeVar("OptionType")

# ---------------------------------------------------------------------------
# Helper widgets
# ---------------------------------------------------------------------------

class _DropdownArrow(ArrowIndicator, ClickableWidget):
    """Visual indicator inside the dropdown button. Clicks fall through to parent."""

    def top_at(self, x, y):
        res = super().top_at(x, y)
        return None if res is self else res

    def ask_focus(self):
        return self.parent.ask_focus()

    def __str__(self):
        return "DropdownArrow"


class _OptionButton(Button):
    """A single selectable option inside the dropdown's panel."""

    def __init__(self, dropdown: "Dropdown", index: int):
        super().__init__(dropdown.display_func(dropdown.options[index]), self._select)
        self._dropdown = dropdown
        self._index = index
        (self.set_alignment(bf.alignment.MIDLEFT)
             .set_auto_wraplength(True)
             .set_unpressed_relief(0).set_pressed_relief(0)
             .set_debug_color("pink"))

    def refresh(self, index: int) -> None:
        """Re-point this button at a (possibly different) option index."""
        self._index = index
        self.set_text(self._dropdown.display_func(self._dropdown.options[index]))
        self.set_bold(index == self._dropdown.current_index)

    def _select(self) -> None:
        self._dropdown.set_by_index(self._index)
        self._dropdown.close()
        self.lose_focus()

    def on_key_down(self, key, event):
        if key == pygame.K_RETURN:
            self._select()
            event.consumed = True
            return
        super().on_key_down(key, event)

    def __str__(self):
        return f"OptionButton({self.text})"


class _OptionColumn(Column):
    """Measure natural row widths; stretch rows only into their final slots."""

    def _rects(self, inner, sizes):
        rects = super()._rects(inner, sizes)
        for child, rect in rects.items():
            rect.left = inner.left
            rect.w = child.constrain_size((inner.width, rect.height),
                                          (inner.width, float("inf")))[0]
        return rects


class _DropDownPanel(ScrollingContainer):
    """Floating panel that holds the option buttons."""

    def __init__(self, dropdown: "Dropdown"):
        self.dropdown = dropdown
        super().__init__(_OptionColumn(4))
        self.set_scroll_x_enabled(False)
        self.set_padding(4)
        self.reveal_selection = False

    def top_at(self, x, y):
        return super().top_at(x, y) if self.dropdown.is_open else None

    def get_debug_outlines(self):
        if not self.visible:
            return
        if any(self.padding):
            yield (self.get_inner_rect(), self.debug_color)
        yield (self.rect, self.debug_color)
        for c in self.children:
            yield from c.get_debug_outlines()

    def open(self)->Self:
        self.dirty_surface = True
        self.reveal_selection = True
        self.show()
        return self
    
    def close(self)->Self:
        self.hide()
        return self
    
    def layout_popup(self, viewport):
        """Called by the root after the dropdown button has been arranged."""
        dropdown = self.dropdown
        margin = max(0, dropdown.panel_screen_margin)
        mx, my = min(margin, viewport.w / 2), min(margin, viewport.h / 2)
        bounds = pygame.FRect(viewport.x + mx, viewport.y + my,
                             max(0, viewport.w - 2 * mx), max(0, viewport.h - 2 * my))
        anchor = dropdown.rect
        gap = max(0, dropdown.panel_gap)
        maximum_height = min(max(0, dropdown.panel_max_height), bounds.h)
        natural = self.measure((bounds.w, maximum_height))
        width = min(bounds.w, max(anchor.w, natural[0]))
        below = max(0, bounds.bottom - max(bounds.top, anchor.bottom + gap))
        above = max(0, min(bounds.bottom, anchor.top - gap) - bounds.top)
        open_below = natural[1] <= below or (natural[1] > above and below >= above)
        height_limit = min(maximum_height, below if open_below else above)
        desired = self.measure((width, height_limit))
        rect = pygame.FRect(anchor.left, anchor.bottom + gap if open_below
                            else anchor.top - gap - desired[1], width, desired[1])
        rect.clamp_ip(bounds)

        # Selection is an index into measured rows, so no provisional child
        # arrangement is needed to reveal it on opening or keyboard navigation.
        if self.reveal_selection and dropdown.current_index is not None:
            rows = dropdown._option_buttons
            index = dropdown.current_index
            top = sum(row.desired_size[1] + self.layout.gap for row in rows[:index])
            bottom = top + rows[index].desired_size[1]
            height = self.get_content_size(rect.size)[1]
            if top < self.scroll.y:
                self.scroll.y = top
            elif bottom > self.scroll.y + height:
                self.scroll.y = max(0, bottom - height)
        self.reveal_selection = False
        self.arrange(rect)

    def handle_event(self, event):
        if not self.dropdown.is_open:
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.dropdown.close()
            event.consumed = True
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.parent_scene:
            mouse = self.get_camera().get_mouse_pos()
            if not self.rect.collidepoint(mouse) and not self.dropdown.rect.collidepoint(mouse):
                self.dropdown.close()
                return
        super().handle_event(event)

# ---------------------------------------------------------------------------
# Dropdown
# ---------------------------------------------------------------------------

class Dropdown(Toggle, Generic[OptionType]):
    """
    Button that reveals a panel of selectable options.

    State model:
      - Toggle's `synced_var` (bool) is the open/closed state. `is_open` reads it.
      - `value_var` (SyncedVar[Any]) is the selected value. External code binds to it.
      - `current_index` mirrors `value_var` as an int; kept in sync internally.
    """

    def __init__(
        self,
        options: list[Any] = None,
        default_value_index: int = None,
        display_func: Callable[[OptionType], str] = None,
        synced_var: SyncedVar[OptionType] = None,   # the *value* var, not the open/close one
    ):
        self.options: list[Any] = options or []
        self.display_func: Callable[[OptionType], str] = display_func or str
        self.on_modify_callback: Callable[[OptionType, int], Any] | None = None
        self.value_var: SyncedVar[OptionType] = synced_var if synced_var is not None else SyncedVar(None)
        self.current_index: int | None = self._resolve_initial_index(default_value_index)

        super().__init__(text=self._current_text(), callback=None, default_value=False)

        # Swap Toggle's indicator for our arrow.
        self.remove(self.indicator)
        self.indicator = (_DropdownArrow(bf.direction.DOWN)
            .set_color((0, 0, 0, 0))
            .set_arrow_color(self.text_color)
            .set_outline_width(0)
            .set_unpressed_relief(0).set_pressed_relief(0))
        self.add(self.indicator)

        # Floating panel. Added so it can reach root; hidden after _populate_panel.
        self._panel = _DropDownPanel(self)
        self.add(self._panel)
        self._option_buttons: list[_OptionButton] = []
        self.panel_gap = 4
        self.panel_screen_margin = 4
        self.panel_max_height = 320
        # Each option registers with StyleManager when construction completes.
        # Scene attachment only refreshes the existing rows.
        self._populate_panel()
        self._panel.close()

        self.value_var.bind(self, self._on_value_var_update)

    def __str__(self) -> str:
        v = self.get_current_value()
        return f"Dropdown[{'' if v is None else v}]"

    # ------------------------------------------------------------------
    # State (open/closed)
    # ------------------------------------------------------------------

    @property
    def is_open(self) -> bool:
        return bool(self.synced_var.value)

    @property
    def trap_focus(self) -> bool:
        return self.is_open

    def open(self) -> None:        self.synced_var.value = True
    def close(self) -> None:       self.synced_var.value = False
    def toggle_open(self) -> None: self.synced_var.value = not self.is_open

    def _focus_candidates(self) -> list[InteractiveWidget]:
        if self.is_open and self.options:
            return [self._option_buttons[self.current_index]]
        return []

    def click(self) -> None:
        """Toggle inherits this — clicking the button toggles the panel."""
        self.toggle_open()

    def _update_state(self, new_value: bool) -> None:
        """SyncedVar's bound callback. Single point where the panel actually opens/closes."""
        self._do_open() if new_value else self._do_close()

    def _do_open(self) -> None:
        if not self.options:
            self.synced_var.value = False
            return
        self.indicator.set_arrow_direction(bf.direction.UP)
        self._refresh_panel_highlight()
        
        if (root := self.get_root()):
            root.attach_to_layer(self._panel, bf.gui.GuiLayer.OVERLAY,
                                 layout_callback=self._panel.layout_popup)
        
        self._panel.open()

    def _do_close(self) -> None:
        self.indicator.set_arrow_direction(bf.direction.DOWN)
        self._panel.close()
        if (root := self._panel.get_root()):
            root.detach_from_layer(self._panel)

    def on_lose_focus(self):
        return super().on_lose_focus()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def do_when_added(self):
        super().do_when_added()
        self._populate_panel()
        self._panel.close()

    def do_when_removed(self):
        self.close()
        super().do_when_removed()

    def on_key_down(self, key, event=None):
        if key == pygame.K_DOWN and self.options:
            new_index = (self.current_index + 1) % len(self.options)
            self.set_by_index(new_index)
            event.consumed = True
        elif key == pygame.K_UP and self.options:
            new_index = (self.current_index - 1) % len(self.options)
            self.set_by_index(new_index)
            event.consumed = True
        elif key in [pygame.K_RETURN, pygame.K_ESCAPE] and self.is_open:
            self.close()
            event.consumed = True
        if not event.consumed:
            super().on_key_down(key, event)
    # ------------------------------------------------------------------
    # Panel sync — reuse existing buttons; add or trim only the difference
    # ------------------------------------------------------------------

    def _populate_panel(self) -> None:
        target = len(self.options)
        current = len(self._option_buttons)

        for i in range(min(current, target)):
            self._option_buttons[i].refresh(i)

        for i in range(current, target):
            btn = _OptionButton(self, i)
            self._option_buttons.append(btn)
            self._panel.add(btn)

        for btn in self._option_buttons[target:]:
            self._panel.remove(btn)
        del self._option_buttons[target:]
        self._panel.reveal_selection = True

    @property
    def panel(self) -> ScrollingContainer:
        """The floating panel, exposed for styling and scrollbar configuration."""
        return self._panel

    def _refresh_panel_highlight(self) -> None:
        for btn in self._option_buttons:
            btn.set_bold(btn._index == self.current_index)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve_initial_index(self, explicit: int | None) -> int | None:
        if not self.options:
            return None
        if explicit is not None:
            return explicit
        if self.value_var.value in self.options:
            return self.options.index(self.value_var.value)
        return 0

    def _current_text(self) -> str:
        if not self.options or self.current_index is None:
            return ""
        return self.display_func(self.options[self.current_index])

    # ------------------------------------------------------------------
    # Options & value API
    # ------------------------------------------------------------------

    def set_options(self, options: list[OptionType], reset_index: bool = True) -> Self:
        self.options = options
        if not options or reset_index or self.current_index is None:
            self.current_index = 0 if options else None
        else:
            self.current_index = min(self.current_index, len(options) - 1)
        self._populate_panel()
        self.set_text(self._current_text())
        if not self.options:
            self.close()
        return self

    def get_current_index(self) -> int | None:
        return self.current_index

    def get_current_value(self) -> OptionType | None:
        if not self.options or self.current_index is None:
            return None
        return self.options[self.current_index]

    def set_by_index(self, index: int) -> Self:
        if not self.options:
            return self
        index = max(0, min(len(self.options) - 1, index))
        if index == self.current_index:
            return self
        self.current_index = index
        value = self.options[index]
        self.set_text(self.display_func(value))
        self.value_var.value = value   # binding no-ops via current_index check
        if self.on_modify_callback:
            self.on_modify_callback(value, index)
        if self.is_open:
            self._refresh_panel_highlight()
            self._panel.reveal_selection = True
        return self

    def set_by_value(self, value: OptionType) -> Self:
        if value in self.options:
            self.set_by_index(self.options.index(value))
        return self

    def set_modify_callback(self, func: Callable[[OptionType, int], Any]) -> Self:
        self.on_modify_callback = func
        return self

    def _on_value_var_update(self, value: OptionType) -> None:
        """Selected value changed externally (or via set_by_index — but that no-ops here)."""
        if value not in self.options:
            return
        new_index = self.options.index(value)
        if new_index == self.current_index:
            return
        self.current_index = new_index
        self.set_text(self.display_func(value))
        self._refresh_panel_highlight()
        self._panel.reveal_selection = True
        if self.on_modify_callback:
            self.on_modify_callback(value, new_index)

    # ------------------------------------------------------------------
    # Sizing
    # ------------------------------------------------------------------

    def get_min_required_size(self) -> tuple[float, float]:
        # Measure widest possible text so the button doesn't resize on selection change.
        max_w, max_h = 0, 0
        style = dataclasses.replace(self._build_style(),bold=True)
        for option in self.options:
            style.text = self.display_func(option)
            w, h = self.renderer.get_min_size(style)
            max_w, max_h = max(max_w, w), max(max_h, h)

        ind = max(self.font.get_height() // 2, 8)
        gap = self.gap if self.text else 0
        w = max_w + ind + gap
        h = max(max_h, ind) + self.unpressed_relief
        return self.compute_min_size(self.expand_rect_with_padding((0, 0, w, h)).size)

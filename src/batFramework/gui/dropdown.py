import pygame
import batFramework as bf
from typing import Self, Callable, Any
from .toggle import Toggle
from .indicator import ArrowIndicator
from .clickableWidget import ClickableWidget
from .syncedVar import SyncedVar
from .container import Container
from .layout import Column
from .widgetUtils import LayoutSlot, distribute_horizontal
from math import ceil
from .button import Button
from .label import Label
from .constraints.constraints import FillX 

# ---------------------------------------------------------------------------
# Inline arrow  (unchanged)
# ---------------------------------------------------------------------------

class _DropdownArrow(ArrowIndicator, ClickableWidget):
    def top_at(self, x, y):
        res = super().top_at(x, y)
        if res == self:
            return None
        return res

    def ask_focus(self):
        return self.parent.ask_focus()

    def __str__(self):
        return "DropdownArrow"


# ---------------------------------------------------------------------------
# Option button inside the panel
# ---------------------------------------------------------------------------

class _OptionButton(Label): 
    def __init__(self, label: str, index: int, dropdown: "Dropdown"):
        super().__init__(label)
        self._index = index
        self._dropdown = dropdown
        self.set_alignment(bf.alignment.LEFT)
        self.set_autoresize_h(True)
        self.set_autoresize_w(False)
        self.set_debug_color("green")
        return
        self.set_unpressed_relief(0).set_pressed_relief(0)
        self.set_outline_width(0).set_border_radius(0)
        self.set_callback(self._on_click)

    def _on_click(self):
        self._dropdown.set_by_index(self._index)
        self._dropdown.close()

    def __str__(self):
        return f"OptionButton({self.text})"


# ---------------------------------------------------------------------------
# Floating panel  (unchanged)
# ---------------------------------------------------------------------------

class _DropDownPanel(Container):
    def __init__(self, dropdown, layout=None, *children):
        self.dropdown = dropdown
        super().__init__(layout, *children)
        self.set_clip_children(True)
        self.set_autoresize_w(False)
        self.set_autoresize_h(True)

    def get_debug_outlines(self):
        if self.visible:
            if any(self.padding):
                yield (self.get_inner_rect(), self.debug_color)
            # else:
            yield (self.rect, self.debug_color)
            for c in self.children:
                yield from c.get_debug_outlines()

    def top_at(self, x, y):
        if not self.dropdown._is_open:
            return None
        return super().top_at(x,y)


# ---------------------------------------------------------------------------
# Dropdown — inherits Toggle for shared layout infrastructure
# ---------------------------------------------------------------------------

class Dropdown(Toggle):
    """
    A button that reveals a floating panel of selectable options when clicked.

    Inherits Toggle for its LayoutSlot-based layout (text + indicator side by
    side with configurable gap/spacing). The ToggleIndicator is replaced with
    a _DropdownArrow, and the slot weights are swapped vs Toggle: text
    stretches (weight=1) while the arrow is fixed (weight=0).

    Toggle's own bool synced_var tracks open/closed state.
    The selected-value synced_var lives as self.value_var.

    Parameters
    ----------
    options             List of values to choose from.
    default_value_index Starting index (None → 0).
    display_func        Converts a value to the string shown on the button.
    synced_var          Optional SyncedVar[Any] kept in sync with selections.
    max_panel_height    Pixel cap for the panel; scrollbar appears beyond that.
    """

    PANEL_MAX_HEIGHT: int = 200

    def __init__(
        self,
        options: list[Any] = None,
        default_value_index: int = None,
        display_func: Callable[[Any], str] = None,
        synced_var: SyncedVar = None,
        max_panel_height: int = None,
    ):
        # ---- Dropdown-specific state (must exist before super().__init__) ----
        self.options: list[Any] = options if options else []
        self.display_func: Callable[[Any], str] = display_func or str
        self.on_modify_callback: Callable[[Any, int], Any] | None = None
        self.value_var: SyncedVar = synced_var if synced_var is not None else SyncedVar(None)
        self.max_panel_height: int = max_panel_height or self.PANEL_MAX_HEIGHT
        self._is_open: bool = False

        # Resolve starting index
        if self.options and default_value_index is None and synced_var is not None:
            try:
                default_value_index = self.options.index(synced_var.value)
            except ValueError:
                default_value_index = 0
        elif self.options and default_value_index is None:
            default_value_index = 0

        self.current_index: int | None = default_value_index
        display_text = (
            self.display_func(self.options[self.current_index])
            if self.options and self.current_index is not None
            else ""
        )

        super().__init__(text=display_text, callback=None, default_value=False)

        # ---- Replace ToggleIndicator with _DropdownArrow --------------------
        self.remove(self.indicator)
        self.indicator: _DropdownArrow = (
            _DropdownArrow(bf.direction.DOWN)
            .set_color((0, 0, 0, 0))
            .set_arrow_color(self.text_color)
            .set_outline_width(0)
            .set_pressed_relief(0).set_unpressed_relief(0)
        )
        self.add(self.indicator)

        # ---- Panel ----------------------------------------------------------
        self._panel: _DropDownPanel = _DropDownPanel(self, Column().set_child_constraints(FillX()))
        self._option_buttons: list[_OptionButton] = []

        self.value_var.bind(self, self._on_value_var_update)

    def __str__(self) -> str:
        val = self.options[self.current_index] if self.options and self.current_index is not None else ""
        return f"Dropdown[{val}]"

    # ------------------------------------------------------------------
    # Toggle overrides
    # ------------------------------------------------------------------

    def click(self) -> None:
        """Redirect Toggle's boolean toggle to panel open/close."""
        self.toggle_open()

    def _update_state(self, new_value: bool) -> None:
        """Called when Toggle's bool synced_var changes externally."""
        if new_value != self._is_open:
            self.open() if new_value else self.close()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def do_when_added(self):
        super().do_when_added()
        root = self.get_root()
        if root and not self._panel.parent:
            root.add(self._panel)
            self._panel.hide()
            self._populate_panel()

    # ------------------------------------------------------------------
    # Panel helpers
    # ------------------------------------------------------------------


    def _populate_panel(self) -> None:
        """Sync option buttons to self.options, reusing instances in place."""
        current_count = len(self._option_buttons)
        target_count = len(self.options)

        for i in range(min(current_count, target_count)): # mutate
            btn = self._option_buttons[i]
            btn._index = i
            btn.set_text(self.display_func(self.options[i]))
            btn.set_bold(i == self.current_index)

        for i in range(current_count, target_count): # add
            btn = _OptionButton(self.display_func(self.options[i]), i, self)
            btn.set_bold(i == self.current_index)
            self._option_buttons.append(btn)
            self._panel.add(btn)

        for btn in self._option_buttons[target_count:]: # remove existing excess
            self._panel.remove(btn)

        self._option_buttons = self._option_buttons[:target_count]

    def _refresh_panel_highlight(self) -> None:
        for btn in self._option_buttons:
            btn.set_bold(btn._index == self.current_index)

    def _position_panel(self) -> None:
        w = self.rect.width
        natural_h = self._panel.get_min_required_size()[1]
        capped_h = min(natural_h, self.max_panel_height)
        self._panel.set_autoresize_h(capped_h == natural_h)
        self._panel.set_size((w, capped_h))
        self._panel.set_position(self.rect.left, self.rect.bottom)

    # ------------------------------------------------------------------
    # Open / close
    # ------------------------------------------------------------------

    def open(self) -> None:
        if self._is_open:
            return
        if not self._panel.parent:
            root = self.get_root()
            if root:
                root.add(self._panel)
        self._is_open = True
        self.synced_var.value = True   # keep Toggle's bool var in sync
        self.indicator.set_arrow_direction(bf.direction.UP)
        self._refresh_panel_highlight()
        self._position_panel()
        self._panel.show()
        self._panel.set_visible(False)
        
    def close(self) -> None:
        if not self._is_open:
            return
        self._is_open = False
        self.synced_var.value = False  # keep Toggle's bool var in sync
        self.indicator.set_arrow_direction(bf.direction.DOWN)
        self._panel.hide()

    def toggle_open(self) -> None:
        self.open() if not self._is_open else self.close()

    def on_lose_focus(self):
        self.close()
        return super().on_lose_focus()

    # ------------------------------------------------------------------
    # Options API
    # ------------------------------------------------------------------

    def set_options(self, options: list[Any], reset_index: bool = True) -> Self:
        self.options = options
        if reset_index:
            self.current_index = 0 if options else None
        elif self.current_index is not None:
            self.current_index = min(self.current_index, len(options) - 1)
        self._populate_panel()
        display_text = (
            self.display_func(self.options[self.current_index])
            if self.options and self.current_index is not None
            else ""
        )
        self.set_text(display_text)
        return self

    # ------------------------------------------------------------------
    # Value API
    # ------------------------------------------------------------------

    def get_current_index(self) -> int | None:
        return self.current_index

    def get_current_value(self) -> Any:
        if self.current_index is None or not self.options:
            return None
        return self.options[self.current_index]

    def set_by_index(self, index: int) -> Self:
        index = max(0, min(len(self.options) - 1, index))
        if index == self.current_index:
            return self
        self.current_index = index
        value = self.options[index]
        self.set_text(self.display_func(value))
        self.value_var.value = value
        if self.on_modify_callback:
            self.on_modify_callback(value, index)
        return self

    def set_by_value(self, value: Any) -> Self:
        if value not in self.options:
            return self
        return self.set_by_index(self.options.index(value))

    def set_modify_callback(self, func: Callable[[Any, int], Any]) -> Self:
        self.on_modify_callback = func
        return self

    def _on_value_var_update(self, value: Any) -> None:
        if value in self.options:
            new_index = self.options.index(value)
            if new_index != self.current_index:
                self.current_index = new_index
                self.set_text(self.display_func(value))
                if self.on_modify_callback:
                    self.on_modify_callback(value, new_index)

    # ------------------------------------------------------------------
    # Sizing — same structure as Toggle but measures across all options
    # ------------------------------------------------------------------

    def get_min_required_size(self) -> tuple[float, float]:
        old_text = self.text
        max_text_w, max_text_h = 0, 0
        for option in self.options:
            self.text = self.display_func(option)
            w, h = self.get_text_size()
            max_text_w = max(max_text_w, w)
            max_text_h = max(max_text_h, h)
        self.text = old_text

        ind_size = max(self.font.get_height() // 2, 8)
        gap = self.gap if self.text else 0

        w = max_text_w + ind_size + gap
        h = max(max_text_h, ind_size) + self.unpressed_relief

        return self.expand_rect_with_padding((0, 0, w, h)).size

    # ------------------------------------------------------------------
    # Layout — Toggle's LayoutSlot machinery with weights swapped:
    # ------------------------------------------------------------------

    def build(self) -> bool:
        res = super(Toggle, self).build()

        local_inner = self.get_local_inner_rect()
        text_w, text_h = self.get_text_size()
        ind_size = max(self.font.get_height() // 2, 8)

        self.indicator.set_size(self.indicator.resolve_size((ind_size, ind_size)))

        has_text = bool(self.text)
        gap = (self.gap if has_text else 0) if self.spacing == bf.spacing.MANUAL else 0

        if self.spacing == bf.spacing.MAX and has_text:
            gap = max(0.0, local_inner.width - text_w - ind_size)

        text_weight = 0 if self.spacing in (bf.spacing.MIN, bf.spacing.MANUAL) else 1

        if has_text:
            slots = [
                LayoutSlot((text_w, text_h), text_weight), 
                LayoutSlot((ind_size, ind_size), 0),
            ]
        else:
            slots = [LayoutSlot((ind_size, ind_size), 0)]

        rects = distribute_horizontal(
            slots=slots,
            rect=local_inner,
            gap=gap,
            alignment=self.alignment,
        )

        if has_text:
            text_rect, ind_rect = rects
            tx = ceil(text_rect.left)
            ty = ceil(text_rect.centery - text_h / 2)
            self.text_rect.update(tx, ty, text_w, text_h)
        else:
            ind_rect = rects[0]

        self.indicator.set_position(
            x=ind_rect.left + self.rect.x,
            y=ind_rect.top + self.rect.y,
        )

        if self._is_open:
            self._position_panel()

        return res
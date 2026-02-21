import pygame
import batFramework as bf
from typing import Self, Callable, Any
from .button import Button
from .indicator import ArrowIndicator
from .clickableWidget import ClickableWidget
from .widget import Widget
from .syncedVar import SyncedVar
from .scrollingContainer import ScrollingContainer
from .layout import Column
from .widgetUtils import LayoutSlot, distribute_horizontal
from math import ceil


# ---------------------------------------------------------------------------
# Inline arrow
# ---------------------------------------------------------------------------

class _DropdownArrow(ArrowIndicator, ClickableWidget):
    def top_at(self, x, y):
        res = super().top_at(x, y)
        if res == self : return None
        return res
    def ask_focus(self):
        return self.parent.ask_focus()

    def __str__(self):
        return "DropdownArrow"


# ---------------------------------------------------------------------------
# Option button inside the panel
# ---------------------------------------------------------------------------

class _OptionButton(Button):
    def __init__(self, label: str, index: int, dropdown: "Dropdown"):
        super().__init__(label)
        self._index = index
        self._dropdown = dropdown
        self.set_alignment(bf.alignment.LEFT)
        self.set_autoresize_h(True)
        self.set_autoresize_w(False)
        self.set_unpressed_relief(0).set_pressed_relief(0)
        self.set_outline_width(0).set_border_radius(0)
        self.set_callback(self._on_click)

    def _on_click(self):
        self._dropdown.set_by_index(self._index)
        self._dropdown.close()

    def __str__(self):
        return f"OptionButton({self.text})"


# ---------------------------------------------------------------------------
# Dropdown
# ---------------------------------------------------------------------------

class Dropdown(Button):
    """
    A button that reveals a floating panel of selectable options when clicked.

    Layout (closed state)
    ---------------------
    [ current option text ▾ ]

    The panel is a persistent child of the dropdown (never destroyed, just
    shown/hidden). Because top_at() recurses into children before checking
    self.rect, clicks on the panel are detected correctly even though it
    extends below the dropdown's own rect.

    Parameters
    ----------
    options             List of values to choose from.
    default_value_index Starting index (None → 0).
    display_func        Converts a value to the string shown on the button.
    synced_var          Optional SyncedVar to keep in sync with selections.
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
        self.options: list[Any] = options if options else []
        self.display_func: Callable[[Any], str] = display_func or str
        self.on_modify_callback: Callable[[Any, int], Any] | None = None
        self.synced_var: SyncedVar = synced_var if synced_var is not None else SyncedVar(None)
        self.max_panel_height: int = max_panel_height or self.PANEL_MAX_HEIGHT
        self._is_open: bool = False
        self.gap: int = 2

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

        super().__init__(display_text, self._on_button_click)

        self.arrow: _DropdownArrow = (
            _DropdownArrow(bf.direction.DOWN)
            .set_color((0, 0, 0, 0))
            .set_arrow_color(self.text_color)
            .set_outline_width(0)
            .set_pressed_relief(0).set_unpressed_relief(0)
        )
        self.add(self.arrow)

        # Build panel once — persists for the lifetime of the dropdown
        self._panel: ScrollingContainer = self._build_panel()
        self._panel.hide()

        self.synced_var.bind(self, self._on_synced_var_update)

    def __str__(self) -> str:
        val = self.options[self.current_index] if self.options and self.current_index is not None else ""
        return f"Dropdown[{val}]"

    # ------------------------------------------------------------------
    # Panel construction  (called once)
    # ------------------------------------------------------------------



    def _build_panel(self) -> ScrollingContainer:
        panel = ScrollingContainer(Column())
        panel.set_outline_width(1)
        panel.set_clip_children(True)
        panel.set_autoresize_w(False)
        panel.set_autoresize_h(True)

        for i, option in enumerate(self.options):
            btn = _OptionButton(self.display_func(option), i, self)
            if i == self.current_index:
                btn.set_bold(True)
            panel.add(btn)

        return panel

    def _refresh_panel_highlight(self) -> None:
        """Update bold state on all option buttons to match current_index."""
        option_buttons = [
            c for c in self._panel.children
            if isinstance(c, _OptionButton)
        ]
        for btn in option_buttons:
            btn.set_bold(btn._index == self.current_index)

    def _position_panel(self) -> None:
        """Size and place the panel just below the dropdown."""
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
        self._is_open = True
        self.arrow.set_arrow_direction(bf.direction.UP)
        self._refresh_panel_highlight()
        self._position_panel()
        if not self._panel.parent:
            r = self.get_root()
            if r:
                r.add(self._panel)
        self._panel.show()
    
    def close(self) -> None:
        if not self._is_open:
            return
        self._is_open = False
        self.arrow.set_arrow_direction(bf.direction.DOWN)
        self._panel.hide()
        if self._panel.parent:
            r = self.get_root()
            if r:
                r.remove(self._panel)


    def toggle_open(self) -> None:
        if self._is_open:
            self.close()
        else:
            self.open()

    # ------------------------------------------------------------------
    # Click / event handling
    # ------------------------------------------------------------------

    def _on_button_click(self) -> None:
        self.toggle_open()

    def on_lose_focus(self):
        self.close()
        return super().on_lose_focus()

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
        self.synced_var.value = value

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

    def _on_synced_var_update(self, value: Any) -> None:
        if value in self.options:
            new_index = self.options.index(value)
            if new_index != self.current_index:
                self.current_index = new_index
                self.set_text(self.display_func(value))
                if self.on_modify_callback:
                    self.on_modify_callback(value, new_index)

    # ------------------------------------------------------------------
    # Sizing — panel is NOT included (it's hidden and has no layout parent)
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

        arrow_size = max(self.font.get_height() // 2, 8)
        total_w = max_text_w + self.gap + arrow_size
        total_h = max_text_h + self.unpressed_relief

        return self.expand_rect_with_padding((0, 0, total_w, total_h)).size

    # ------------------------------------------------------------------
    # Layout — text left (stretches), arrow pinned right
    # ------------------------------------------------------------------

    def build(self) -> bool:
        res = super().build()

        local_inner = self.get_local_inner_rect()
        text_w, text_h = self.get_text_size()
        arrow_size = max(self.font.get_height() // 2, 8)

        slots = [
            LayoutSlot(size=(text_w, text_h), weight=1),
            LayoutSlot(size=(arrow_size, arrow_size), weight=0),
        ]

        rects = distribute_horizontal(
            slots=slots,
            rect=local_inner,
            gap=self.gap,
            alignment=self.alignment,
        )

        text_rect, arrow_rect = rects

        tx = ceil(text_rect.left)
        ty = ceil(text_rect.centery - text_h / 2)
        self.text_rect.update(tx, ty, text_w, text_h)

        self.arrow.set_size(self.arrow.resolve_size((arrow_size, arrow_size)))
        self.arrow.set_position(
            x=arrow_rect.left + self.rect.x,
            y=arrow_rect.top + self.rect.y,
        )

        # Keep panel flush with the dropdown's bottom edge if open
        if self._is_open:
            self._position_panel()

        return res
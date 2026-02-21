import batFramework as bf
import pygame
from typing import Self, Callable, Any
from .button import Button
from .label import Label
from .indicator import ArrowIndicator
from .clickableWidget import ClickableWidget
from .widget import Widget
from .syncedVar import SyncedVar
from .widgetUtils import LayoutSlot, distribute_horizontal
from math import ceil


class MyArrow(ArrowIndicator, ClickableWidget):
    def top_at(self, x, y):
        return Widget.top_at(self, x, y)

    def ask_focus(self):
        return self.parent.ask_focus()

    def __str__(self):
        return "SelectorArrow"


class Selector(Button):
    def __init__(
        self,
        name: str = "",
        options: list[Any] = None,
        default_value_index: int = None,
        display_func: Callable[[Any], str] = None,
        synced_var: SyncedVar = None,
    ):
        self.allow_cycle = False
        self.current_index = default_value_index
        self.on_modify_callback: Callable[[Any, int], Any] = None
        self.options = options if options else []
        self.display_func =  str if display_func is None else display_func 
        self.gap: float | int = 2
        self.spacing: bf.spacing = bf.spacing.MANUAL
        self.synced_var = synced_var if synced_var is not None else SyncedVar(None)
        display_text = ""
        super().__init__("")

        self.label: Label = Label(name).set_autoresize(True)
        self.label.top_at = lambda *args : None
        self.add(self.label)

        self.left_indicator: MyArrow = (
            MyArrow(bf.direction.LEFT)
            .set_color((0, 0, 0, 0))
            .set_arrow_color(self.text_color)
            .set_callback(lambda: self.set_by_index(self.get_current_index() - 1))
            .set_outline_width(0)
        )

        self.right_indicator: MyArrow = (
            MyArrow(bf.direction.RIGHT)
            .set_color((0, 0, 0, 0))
            .set_arrow_color(self.text_color)
            .set_callback(lambda: self.set_by_index(self.get_current_index() + 1))
            .set_outline_width(0)

        )

        self.add(self.left_indicator, self.right_indicator)
        self.set_clip_children(False)

        if self.options and default_value_index is None and synced_var is not None:
            display_text = self.display_func(synced_var.value)
            default_value_index = self.options.index(synced_var.value)
        elif self.options:
            if default_value_index is None:
                default_value_index = 0
            display_text = self.display_func(self.options[default_value_index])

        self.current_index = default_value_index
        self.set_text(display_text)

        # Bind synced var so external changes propagate to this widget
        self.synced_var.bind(self, self._on_synced_var_update)

    def __str__(self):
        return f"Selector[{self.options[self.current_index] if self.options else ''}]"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_text_widget(self):
        if self.options:
            self.set_text(self.display_func(self.options[self.current_index]))
        else:
            self.set_text("")

    def _on_synced_var_update(self, value: Any):
        if value in self.options:
            self.current_index = self.options.index(value)
            self._update_text_widget()
            self._update_arrow_states()
            if self.on_modify_callback:
                self.on_modify_callback(value, self.current_index)

    def _update_arrow_states(self):
        if not self.allow_cycle:
            if self.current_index <= 0:
                self.left_indicator.disable()
            else:
                self.left_indicator.enable()

            if self.current_index >= len(self.options) - 1:
                self.right_indicator.disable()
            else:
                self.right_indicator.enable()

    # ------------------------------------------------------------------
    # Configuration API
    # ------------------------------------------------------------------

    def set_gap(self, value: int | float) -> Self:
        value = max(0, value)
        if value != self.gap:
            self.gap = value
            self.dirty_shape = True
        return self

    def set_spacing(self, spacing: bf.spacing) -> Self:
        if spacing != self.spacing:
            self.spacing = spacing
            self.dirty_shape = True
        return self

    def set_arrow_color(self, color) -> Self:
        self.left_indicator.set_arrow_color(color)
        self.right_indicator.set_arrow_color(color)
        return self

    def set_allow_cycle(self, value: bool) -> Self:
        if value != self.allow_cycle:
            self.allow_cycle = value
            self.dirty_surface = True
            self._update_arrow_states()
        return self

    def set_text_color(self, color) -> Self:
        super().set_text_color(color)
        return self

    def set_modify_callback(self, func: Callable[[Any, int], Any]) -> Self:
        self.on_modify_callback = func
        return self

    def set_tooltip_text(self, text) -> Self:
        self.left_indicator.set_tooltip_text(text)
        self.right_indicator.set_tooltip_text(text)
        return super().set_tooltip_text(text)

    def set_visible(self, value: bool) -> Self:
        self.left_indicator.set_visible(value)
        self.right_indicator.set_visible(value)
        return super().set_visible(value)

    def disable(self):
        super().disable()
        self.left_indicator.disable()
        self.right_indicator.disable()
        return self

    def enable(self):
        super().enable()
        self.left_indicator.enable()
        self.right_indicator.enable()
        self._update_arrow_states()
        return self

    # ------------------------------------------------------------------
    # Value access
    # ------------------------------------------------------------------

    def get_current_index(self) -> int:
        return self.current_index

    def set_by_index(self, index: int) -> Self:
        if self.allow_cycle:
            index = index % len(self.options)
        else:
            index = max(min(len(self.options) - 1, index), 0)

        if index == self.current_index:
            return self

        self.current_index = index
        value = self.options[self.current_index]
        display_text = self.display_func(value)
        self.set_text(display_text)

        self.synced_var.value = value

        if self.on_modify_callback:
            self.on_modify_callback(value, self.current_index)

        self._update_arrow_states()
        return self

    def set_by_value(self, value: str) -> Self:
        if not self.is_enabled:
            return self
        if value not in self.options:
            return self
        index = self.options.index(value)
        self.set_by_index(index)
        return self

    # ------------------------------------------------------------------
    # Sizing
    # ------------------------------------------------------------------

    def get_min_required_size(self) -> tuple[float, float]:
        # Measure the widest rendered text across all options without
        # triggering dirty flags — temporarily swap self.text in-place.
        old_text = self.text
        max_text_w, max_text_h = 0, 0
        for option in self.options:
            self.text = self.display_func(option)
            w, h = self.get_text_size()
            max_text_w = max(max_text_w, w)
            max_text_h = max(max_text_h, h)
        self.text = old_text

        # Arrow size is derived from text height (square)

        arrow_size = max(self.font.get_height() // 2, 10)

        gap = self.gap

        label_w, label_h = self.label.get_min_required_size() if self.label.text else (0, 0)
        label_gap = gap if self.label.text else 0

        total_w = label_w + label_gap + arrow_size + gap + max_text_w + gap + arrow_size
        total_h = max(max_text_h, label_h) + self.unpressed_relief
        total_h += max(
            self.right_indicator.outline_width, self.left_indicator.outline_width
        )

        return self.expand_rect_with_padding((0, 0, total_w, total_h)).size

    # ------------------------------------------------------------------
    # Layout via build() — mirrors Slider/Toggle pattern
    # ------------------------------------------------------------------

    def build(self) -> bool:
        res = super().build()

        local_inner = self.get_local_inner_rect()
        text_w, text_h = self.get_text_size()

        # Arrow size: square whose side equals the inner height
        arrow_size = arrow_size = max(self.font.get_height() // 2, 10)
        arrow_slot_size = (arrow_size, arrow_size)

        # Resolve gap
        if self.spacing == bf.spacing.MANUAL:
            gap = self.gap
        elif self.spacing == bf.spacing.MIN:
            gap = 0
        elif self.spacing == bf.spacing.MAX:
            gap = max(0.0, (local_inner.width - text_w - arrow_size * 2) / 2)
        else:
            gap = self.gap

        # Build slots: optional label | left arrow | text (stretches) | right arrow
        label_w, label_h = self.label.get_min_required_size() if self.label.text else (0, 0)

        slots = []
        if self.label.text:
            slots.append(LayoutSlot(size=(label_w, label_h), weight=0))  # name label
        slots += [
            LayoutSlot(size=arrow_slot_size, weight=0),   # left arrow
            LayoutSlot(size=(text_w, text_h), weight=1),  # text (fills leftover)
            LayoutSlot(size=arrow_slot_size, weight=0),   # right arrow
        ]

        rects = distribute_horizontal(
            slots=slots,
            rect=local_inner,
            gap=gap,
            alignment=self.alignment,
        )

        # Unpack rects depending on whether label is present
        if self.label.text:
            label_rect, left_rect, text_rect, right_rect = rects
        else:
            left_rect, text_rect, right_rect = rects

        # ---- Text rect (LOCAL surface coords) -------------------------
        tx = ceil(text_rect.left)
        ty = ceil(text_rect.centery - text_h / 2)
        self.text_rect.update(tx, ty, text_w, text_h)

        # ---- Label position (WORLD coords) ----------------------------
        if self.label.text:
            self.label.set_size(self.label.resolve_size((label_w, label_h)))
            self.label.set_position(
                x=label_rect.left + self.rect.x,
                y=label_rect.top + self.rect.y,
            )

        # ---- Arrow sizes and positions (WORLD coords) -----------------
        left_size = self.left_indicator.resolve_size(arrow_slot_size)
        self.left_indicator.set_size(left_size)
        self.left_indicator.set_position(
            x=left_rect.left + self.rect.x,
            y=left_rect.top + self.rect.y,
        )

        right_size = self.right_indicator.resolve_size(arrow_slot_size)
        self.right_indicator.set_size(right_size)
        self.right_indicator.set_position(
            x=right_rect.left + self.rect.x,
            y=right_rect.top + self.rect.y,
        )

        return res

    # ------------------------------------------------------------------
    # Keyboard input
    # ------------------------------------------------------------------

    def on_key_down(self, key: int, event) -> None:
        if not self.is_enabled:
            return
        key_actions = {
            pygame.K_RIGHT: self.right_indicator,
            pygame.K_SPACE: self.right_indicator,
            pygame.K_LEFT: self.left_indicator,
        }
        indicator = key_actions.get(key)
        if indicator and indicator.visible and indicator.is_enabled:
            indicator.on_click_down(1, event)
            event.consumed = True

    def on_key_up(self, key: int, event) -> None:
        if not self.is_enabled:
            return
        key_actions = {
            pygame.K_RIGHT: self.right_indicator,
            pygame.K_SPACE: self.right_indicator,
            pygame.K_LEFT: self.left_indicator,
        }
        indicator = key_actions.get(key)
        if indicator and indicator.visible and indicator.is_enabled:
            indicator.on_click_up(1, event)
            event.consumed = True
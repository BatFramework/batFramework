import batFramework as bf
import pygame
from typing import Self, Callable, Any
from .button import Button
from .indicator import ArrowIndicator
from .clickableWidget import ClickableWidget
from .widget import Widget
from .syncedVar import SyncedVar

class MyArrow(ArrowIndicator, ClickableWidget):
    def top_at(self, x, y):
        return Widget.top_at(self, x, y)

    def get_focus(self):
        return self.parent.get_focus()

    def __str__(self):
        return "SelectorArrow"

class Selector(Button):
    def __init__(self, options: list[Any] = None, default_value_index: int = None, display_func: Callable[[Any], str] = None,synced_var: SyncedVar = None):
        self.allow_cycle = False
        self.current_index = default_value_index
        self.on_modify_callback: Callable[[Any, int], Any] = None
        self.options = options if options else []
        self.display_func = display_func or str
        self.gap: int = 2
        self.synced_var = synced_var if synced_var is not None else SyncedVar(None)
        display_text = ""

        super().__init__("")

        self.left_indicator: MyArrow = (MyArrow(bf.direction.LEFT)
            .set_color((0, 0, 0, 0)).set_arrow_color(self.text_widget.text_color)
            .set_callback(lambda: self.set_by_index(self.get_current_index() - 1))
        )

        self.right_indicator: MyArrow = (MyArrow(bf.direction.RIGHT)
            .set_color((0, 0, 0, 0)).set_arrow_color(self.text_widget.text_color)
            .set_callback(lambda: self.set_by_index(self.get_current_index() + 1))
        )

        self.add(self.left_indicator, self.right_indicator)
        self.set_clip_children(False)

        if self.options and default_value_index is None and synced_var is not None:
            display_text = display_func(synced_var.value)
            default_value_index = self.options.index(synced_var.value)
        elif self.options:
            if default_value_index is None:
                default_value_index= 0
            display_text = self.display_func(self.options[default_value_index])
        self.current_index = default_value_index
        self.set_text(display_text)

    def __str__(self):
        return f"Selector[{self.options[self.current_index] if self.options else ''}]"

    def _update_text_widget(self):
        if self.options:
            display_text = self.display_func(self.options[self.current_index])
            self.text_widget.set_text(display_text)
        else:
            self.text_widget.set_text("")

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

    def set_gap(self, value: int) -> Self:
        self.gap = value
        self.dirty_shape = True
        return self

    def set_arrow_color(self, color) -> Self:
        self.left_indicator.set_arrow_color(color)
        self.right_indicator.set_arrow_color(color)
        return self

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

    def set_tooltip_text(self, text) -> Self:
        self.left_indicator.set_tooltip_text(text)
        self.right_indicator.set_tooltip_text(text)
        return super().set_tooltip_text(text)

    def get_min_required_size(self) -> tuple[float, float]:
        old_text = self.text_widget.get_text()
        max_size = (0, 0)
        for option in self.options:
            self.text_widget.set_text(self.display_func(option))
            size = self.text_widget.get_min_required_size()
            max_size = (max(max_size[0], size[0]), max(max_size[1], size[1]))
        self.text_widget.set_text(old_text)

        # total_height = max(self.font_object.get_height() + 1, max_size[1] * 1.5)
        total_height = max_size[1] if max_size[1] > 16 else max_size[1]*1.5
        total_height += self.unpressed_relief
        total_height += max(self.right_indicator.outline_width, self.left_indicator.outline_width)

        total_width = total_height * 2 + max_size[0] + self.gap * 2

        return self.expand_rect_with_padding((0, 0, total_width, total_height)).size

    def _align_content(self):
        padded = self.get_inner_rect()
        indicator_height = padded.h
        self.left_indicator.set_size((indicator_height, indicator_height))
        self.right_indicator.set_size((indicator_height, indicator_height))

        self.left_indicator.set_position(padded.left, None)
        self.left_indicator.set_center(None, padded.centery)

        right_size = self.right_indicator.rect.size
        self.right_indicator.set_position(padded.right - right_size[0], None)
        self.right_indicator.set_center(None, padded.centery)

    def apply_post_updates(self, skip_draw=False):
        super().apply_post_updates(skip_draw)
        self._align_content()

    def get_current_index(self) -> int:
        return self.current_index

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

        if not self.allow_cycle:
            if index == 0:
                self.left_indicator.disable()
            else:
                self.left_indicator.enable()
            if index == len(self.options) - 1:
                self.right_indicator.disable()
            else:
                self.right_indicator.enable()

        return self


    def set_by_value(self, value: str) -> Self:
        if not self.is_enabled:
            return self
        if value not in self.options:
            return self
        index = self.options.index(value)
        self.set_by_index(index)
        return self
    
    def on_key_down(self, key: int,event) -> None:
        if not self.is_enabled:
            return
        key_actions = {
            pygame.K_RIGHT: self.right_indicator,
            pygame.K_SPACE: self.right_indicator,
            pygame.K_LEFT: self.left_indicator,
        }
        indicator = key_actions.get(key)
        if indicator and indicator.visible and indicator.is_enabled:
            indicator.on_click_down(1,event)
            event.consumed = True

    def on_key_up(self, key: int,event) -> None:
        if not self.is_enabled:
            return 
        key_actions = {
            pygame.K_RIGHT: self.right_indicator,
            pygame.K_SPACE: self.right_indicator,
            pygame.K_LEFT: self.left_indicator,
        }
        indicator = key_actions.get(key)
        if indicator and indicator.visible and indicator.is_enabled:
            indicator.on_click_up(1,event)
            event.consumed = True

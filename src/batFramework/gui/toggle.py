from .button import Button
from .indicator import Indicator, ToggleIndicator
import pygame
import batFramework as bf
from typing import Self



class Toggle(Button):
    def __init__(self, text: str, default_value: bool = False,callback=None) -> None:
        self.value: bool = default_value
        self.on_toggle = None
        self.indicator: Indicator = ToggleIndicator(default_value)
        self.gap: float | int = 0
        super().__init__(text, self.toggle)
        self.add_child(self.indicator)
        self.set_gap(int(max(4, self.get_content_width() / 3)))
        self.set_toggle_callback(callback)

    def set_gap(self, value: int | float) -> Self:
        if value < 0:
            return self
        self.gap = value
        self.build()
        if self.parent:
            self.parent.children_modified()
        return self

    def to_string_id(self) -> str:
        return f"Toggle({self.value})"

    def toggle(self) -> None:
        self.value = not self.value
        self.build()
        if self.on_toggle:
            self.on_toggle(self.value)

    def set_toggle_callback(self, callback) -> Self:
        self.on_toggle = callback
        return self

    def _build_layout(self) -> None:
        self.indicator.set_value(self.value)
        self.indicator.set_size(self._text_rect.h,self._text_rect.h)
        size = (
            0,
            0,
            self._text_rect.w + self.indicator.rect.w + self.gap,
            max(self._text_rect.h, self.indicator.rect.h),
        )

        required_rect = self.inflate_rect_by_padding(size)

        if self.autoresize and (self.rect.size != required_rect.size):
            self.set_size(*required_rect.size)
            return

        required_rect = self.get_content_rect()
        required_rect_rel = self.get_content_rect_rel()

        self._text_rect.midleft = required_rect_rel.midleft
        r = self.indicator.rect.copy()
        r.midleft = required_rect.move(self._text_rect.w + self.gap, 0).midleft
        self.indicator.set_position(*r.topleft)

        self.surface.blit(self._text_surface, self._text_rect)

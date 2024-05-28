from .button import Button
from .indicator import Indicator, ToggleIndicator
import batFramework as bf
from typing import Self
import pygame


class Toggle(Button):
    def __init__(self, text: str, default_value: bool = False, callback=None) -> None:
        self.value: bool = default_value
        self.indicator: ToggleIndicator = ToggleIndicator(default_value)
        self.gap: float | int = 0
        super().__init__(text, callback)
        self.add(self.indicator)
        self.set_gap(int(max(4, self.get_padded_width() / 3)))

    def set_value(self, value: bool, do_callback=False) -> Self:
        self.value = value
        self.indicator.set_value(value)
        self.dirty_surface = True
        if do_callback and self.callback:
            self.callback(self.value)
        return self

    def click(self) -> None:
        self.set_value(not self.value, True)
        # if self.callback is not None:
        bf.Timer(duration=0.3, end_callback=self._safety_effect_end).start()

    def set_gap(self, value: int | float) -> Self:
        value = max(0, value)
        if value == self.gap : return self
        self.gap = value
        self.dirty_shape = True
        return self

    def to_string_id(self) -> str:
        return f"Toggle({self.value})"

    def toggle(self) -> None:
        self.set_value(not self.value, do_callback=True)

    def get_min_required_size(self) -> tuple[float, float]:
        if not self.font_object:
            return (0, 0)
        w, h = self.font_object.size(self.text)
        return self.inflate_rect_by_padding(
            (0, 0, w + self.gap + self.indicator.rect.w, max(h, self.indicator.rect.h))
        ).size

    def _build_layout(self) -> None:
        self.text_rect.size = self.font_object.size(self.text)
        indicator_height = self.text_rect.h
        tmp_rect = pygame.FRect(
            0,0,
            self.text_rect.w + indicator_height + self.gap, indicator_height,
        )
        if self.autoresize:
            target_rect = self.inflate_rect_by_padding(tmp_rect)
            if self.rect.size != target_rect.size:
                self.set_size(target_rect.size)
                self.build()
                return

        padded = self.get_padded_rect().move(-self.rect.x,-self.rect.y - self.get_relief()/2)
        self.indicator.set_size((indicator_height,indicator_height))
        
        self.align_text(tmp_rect,padded,self.alignment)
        self.text_rect.midleft = tmp_rect.midleft
        # indic_copy = self.indicator.rect.copy()
        # indic_copy.midleft = (
        #     padded
        #     .move(self.text_rect.w + self.gap, self.relief - self.get_relief())
        #     .midleft
        # )
        # self.indicator.set_position(*indic_copy.move(*self.rect.topleft).topleft)

    def paint(self) -> None:
        super().paint()
        padded = self.get_padded_rect().move(-self.rect.x,-self.rect.y - self.get_relief()/2)
        indic_copy = self.indicator.rect.copy()
        indic_copy.midright = padded.midright
        self.indicator.set_position(*indic_copy.move(*self.rect.topleft).topleft)


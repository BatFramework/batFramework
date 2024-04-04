from .button import Button
from .indicator import Indicator, ToggleIndicator
import pygame
import batFramework as bf
from typing import Self



class Toggle(Button):
    def __init__(self, text: str, default_value: bool = False,callback=None) -> None:
        self.value: bool = default_value
        self.indicator: Indicator = ToggleIndicator(default_value)
        self.gap: float | int = 0
        super().__init__(text, callback)
        self.add_child(self.indicator)
        self.set_gap(int(max(4, self.get_content_width() / 3)))

    def set_value(self,value:bool,do_callback=False)->Self:
        self.value = value
        self.build()
        if do_callback: self.callback(self.value)
        return self

    def click(self) -> None:
        if self.callback is not None:
            self.set_value(not self.value,True)
            bf.Timer(duration=0.3,end_callback=self._safety_effect_end).start()

        
    def set_gap(self, value: int | float) -> Self:
        if value < 0:
            return self
        self.gap = value
        self.build()
        if self.parent:
            self.parent.notify()
        return self

    def to_string_id(self) -> str:
        return f"Toggle({self.value})"

    def toggle(self) -> None:
        self.set_value(not self.value,do_callback = True)


    def _build_layout(self) -> None:
        self.indicator.set_value(self.value)
        self.indicator.set_size(self.text_rect.h,self.text_rect.h)
        size = (
            0,
            0,
            self.text_rect.w + self.indicator.rect.w + self.gap,
            max(self.text_rect.h, self.indicator.rect.h),
        )

        required_rect = self.inflate_rect_by_padding(size)

        if self.autoresize and (self.rect.size != required_rect.size):
            self.set_size(*required_rect.size)
            return

        required_rect = self.get_content_rect()
        required_rect_rel = self.get_content_rect_rel()

        self.text_rect.midleft = required_rect_rel.midleft
        r = self.indicator.rect.copy()
        r.midleft = required_rect.move(self.text_rect.w + self.gap, 0).midleft
        self.indicator.set_position(*r.topleft)

        self.surface.blit(self.text_surface, self.text_rect)

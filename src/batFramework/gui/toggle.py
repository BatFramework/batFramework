from .button import Button
from .indicator import Indicator, ToggleIndicator
import batFramework as bf
from typing import Self
import pygame


class Toggle(Button):
    def __init__(self, text: str, callback=None,default_value: bool = False) -> None:
        self.value: bool = default_value
        self.indicator: ToggleIndicator = ToggleIndicator(default_value)
        self.gap: float | int = 0
        super().__init__(text, callback)
        self.add(self.indicator)
        # self.set_gap(int(max(4, self.get_padded_width() / 3)))

    def set_value(self, value: bool, do_callback=False) -> Self:
        self.value = value
        self.indicator.set_value(value)
        self.dirty_surface = True
        if do_callback and self.callback:
            self.callback(self.value)
        return self

    def click(self) -> None:
        self.set_value(not self.value, True)

    def set_gap(self, value: int | float) -> Self:
        value = max(0, value)
        if value == self.gap : return self
        self.gap = value
        self.dirty_shape = True
        return self

    def __str__(self) -> str:
        return f"Toggle({self.value})"

    def toggle(self) -> None:
        self.set_value(not self.value, do_callback=True)

    def get_min_required_size(self) -> tuple[float, float]:
        if not self.text_rect:
            params = {
                "font_name": self.font_object.name,
                "text": self.text,
                "antialias": False,
                "color": "white",
                "bgcolor": "black",  # if (self.has_alpha_color() or self.draw_mode == bf.drawMode.TEXTURED) else self.color,
                "wraplength": int(self.get_padded_width()) if self.auto_wraplength else 0,
            }
            self.text_rect.size = self._render_font(params).get_size()
        w,h = self.text_rect.size
        size = w + self.font_object.point_size + (self.gap if self.text else 0), max(h,self.font_object.point_size)
        return self.inflate_rect_by_padding((0,0,*size)).size

        
    def _build_layout(self) -> None:

        gap = self.gap if self.text else 0 
        params = {
            "font_name": self.font_object.name,
            "text": self.text,
            "antialias": False,
            "color": "white",
            "bgcolor": "black",  # if (self.has_alpha_color() or self.draw_mode == bf.drawMode.TEXTURED) else self.color,
            "wraplength": int(self.get_padded_width()) if self.auto_wraplength else 0,
        }
        self.text_rect.size = self._render_font(params).get_size()
        indicator_height = self.font_object.point_size

        self.indicator.set_size((indicator_height,indicator_height))

        tmp_rect = pygame.FRect(0,0,self.text_rect.w + indicator_height + gap, self.text_rect.h)
        
        if self.autoresize:
            target_rect = self.inflate_rect_by_padding(tmp_rect)
            if self.rect.size != target_rect.size:
                self.set_size(target_rect.size)
                self.build()
                return

        padded = self.get_padded_rect().move(-self.rect.x,-self.rect.y)
        
        self.align_text(tmp_rect,padded,self.alignment)
        self.text_rect.midleft = tmp_rect.midleft

        self.indicator.set_position(*self.text_rect.move(self.rect.x+gap,self.rect.y + (self.text_rect.h /2) - indicator_height/2).topright)

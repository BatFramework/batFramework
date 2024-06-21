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
        self.spacing :bf.spacing = bf.spacing.MANUAL 
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

    def set_spacing(self,spacing:bf.spacing)->Self:
        if spacing == self.spacing : return self
        self.spacing = spacing
        self.dirty_shape = True
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
        size = max(self.indicator.rect.w,w + self.font_object.point_size + (self.gap if self.text else 0)), max(h,self.font_object.point_size,self.indicator.rect.h)
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

        
        tmp_rect = pygame.FRect(0,0,self.text_rect.w + gap + indicator_height , self.text_rect.h)


        if self.autoresize_h or self.autoresize_w: 
            target_rect = self.inflate_rect_by_padding(tmp_rect)
            if not self.autoresize_w : target_rect.w = self.rect.w
            if not self.autoresize_h : target_rect.h = self.rect.h
            if self.rect.size != target_rect.size:
                self.set_size(target_rect.size)
                self.build()
                return
            
        padded = self.get_padded_rect().move(-self.rect.x,-self.rect.y)
        
        self.align_text(tmp_rect,padded,self.alignment)
        self.text_rect.midleft = tmp_rect.midleft
        if self.text : 
            match self.spacing:
                case bf.spacing.MAX:
                    gap = padded.w - self.text_rect.w - self.indicator.rect.w
                case bf.spacing.MIN:
                    gap = 0
                case bf.spacing.HALF:
                    gap = (padded.w)/2 - self.text_rect.w

        self.indicator.set_position(
            *self.text_rect.move(
                self.rect.x+gap,
                self.rect.y + (self.text_rect.h /2) - self.indicator.rect.h/2
            ).topright
        )

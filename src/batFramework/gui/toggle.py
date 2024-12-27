from .button import Button
from .indicator import Indicator, ToggleIndicator
from .shape import Shape
import batFramework as bf
from typing import Self,Callable,Any
import pygame
from math import ceil

class Toggle(Button):
    def __init__(self, text: str = "", callback : Callable[[bool],Any]=None, default_value: bool = False) -> None:
        self.value: bool = default_value
        self.indicator: ToggleIndicator = ToggleIndicator(default_value)
        self.gap: float | int = 0
        self.spacing: bf.spacing = bf.spacing.MANUAL
        super().__init__(text, callback)
        self.add(self.indicator)
        self.set_clip_children(False)

    def set_visible(self, value: bool) -> Self:
        self.indicator.set_visible(value)
        return super().set_visible(value)

    def set_value(self, value: bool, do_callback=False) -> Self:
        self.value = value
        self.indicator.set_value(value)
        self.dirty_surface = True
        if do_callback and self.callback:
            self.callback(self.value)
        return self

    def set_spacing(self, spacing: bf.spacing) -> Self:
        if spacing == self.spacing:
            return self
        self.spacing = spacing
        self.dirty_shape = True
        return self

    def click(self) -> None:
        self.set_value(not self.value, True)

    def set_gap(self, value: int | float) -> Self:
        value = max(0, value)
        if value == self.gap:
            return self
        self.gap = value
        self.dirty_shape = True
        return self

    def __str__(self) -> str:
        return f"Toggle({self.value})"

    def toggle(self) -> None:
        self.set_value(not self.value, do_callback=True)

    def get_min_required_size(self) -> tuple[float, float]:
        gap = self.gap if self.text else 0
        if not self.text_rect:
            self.text_rect.size = self._get_text_rect_required_size()
        w, h = self.text_rect.size
        h+=self.unpressed_relief
        return self.inflate_rect_by_padding((0, 0, w + gap + self.indicator.get_min_required_size()[1], h)).size



    def _build_composed_layout(self,other:Shape):

        gap = self.gap if self.text else 0
        full_rect = self.text_rect.copy()

        other_height = min(self.text_rect.h, self.font_object.get_height()+1)
        other.set_size_if_autoresize((other_height,other_height))
        
        full_rect.w += other.rect.w + gap
        
        if self.autoresize_h or self.autoresize_w:
            target_rect = self.inflate_rect_by_padding((0, 0, *full_rect.size))
            target_rect.h += self.unpressed_relief # take into account the relief when calculating target rect
            tmp = self.rect.copy()
            self.set_size_if_autoresize(target_rect.size)
            if self.rect.size != tmp.size:
                self.apply_updates(skip_draw=True)
                return

        self._align_composed(other)

    def _align_composed(self,other:Shape):
        
        full_rect = self.get_local_padded_rect()
        left_rect = self.text_rect
        right_rect = other.rect
        gap = {
            bf.spacing.MIN: 0,
            bf.spacing.HALF: (full_rect.width - left_rect.width - right_rect.width) // 2,
            bf.spacing.MAX: full_rect.width - left_rect.width - right_rect.width,
            bf.spacing.MANUAL: self.gap
        }.get(self.spacing, 0)

        gap = max(0, gap)
        combined_width = left_rect.width + right_rect.width + gap

        group_x = {
            bf.alignment.LEFT: full_rect.left,
            bf.alignment.MIDLEFT: full_rect.left,
            bf.alignment.RIGHT: full_rect.right - combined_width,
            bf.alignment.MIDRIGHT: full_rect.right - combined_width,
            bf.alignment.CENTER: full_rect.centerx - combined_width // 2
        }.get(self.alignment, full_rect.left)

        left_rect.x, right_rect.x = group_x, group_x + left_rect.width + gap

        if self.alignment in {bf.alignment.TOP, bf.alignment.TOPLEFT, bf.alignment.TOPRIGHT}:
            left_rect.top = right_rect.top = full_rect.top
        elif self.alignment in {bf.alignment.BOTTOM, bf.alignment.BOTTOMLEFT, bf.alignment.BOTTOMRIGHT}:
            left_rect.bottom = right_rect.bottom = full_rect.bottom
        else:
            left_rect.centery = right_rect.centery = full_rect.centery

        right_rect.move_ip(*self.rect.topleft)



    def _build_layout(self) -> None:
        self.text_rect.size = self._get_text_rect_required_size()
        self._build_composed_layout(self.indicator)



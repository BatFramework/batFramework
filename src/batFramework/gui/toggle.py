from .button import Button
from .indicator import Indicator, ToggleIndicator
import batFramework as bf
from typing import Self,Callable,Any
import pygame


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
        if not self.text_rect:
            self.text_rect.size = self._get_text_rect_required_size()
        size = (
            max(
                self.indicator.get_min_required_size()[0],
                self.text_rect.w + self.font_object.point_size + (self.gap if self.text else 0),
            ),
            self.text_rect.h+self.unpressed_relief,
        )
        return self.inflate_rect_by_padding((0, 0, *size)).size

    def _build_layout(self) -> None:
        gap = self.gap if self.text else 0
        self.text_rect.size = self._get_text_rect_required_size()

        #right part size
        right_part_height = min(self.text_rect.h, self.font_object.point_size)
        self.indicator.set_size_if_autoresize((right_part_height,right_part_height))

        #join left and right
        joined_rect = pygame.FRect(
            0, 0, self.text_rect.w + gap + self.indicator.rect.w, self.text_rect.h 
        )

        if self.autoresize_h or self.autoresize_w:
            target_rect = self.inflate_rect_by_padding(joined_rect)
            target_rect.h += self.unpressed_relief
            if not self.autoresize_w:
                target_rect.w = self.rect.w
            if not self.autoresize_h:
                target_rect.h = self.rect.h
            if self.rect.size != target_rect.size:
                self.set_size(target_rect.size)
                self.apply_updates()

        # ------------------------------------ size is ok

        offset = self._get_outline_offset() if self.show_text_outline else (0,0)
        padded_rect = self.get_padded_rect()
        padded_relative = padded_rect.move(-self.rect.x, -self.rect.y)

        self.align_text(joined_rect, padded_relative.move( offset), self.alignment)
        self.text_rect.midleft = joined_rect.midleft

        if self.text:
            match self.spacing:
                case bf.spacing.MAX:
                    gap = padded_relative.right - self.text_rect.right - self.indicator.rect.w
                case bf.spacing.MIN:
                    gap = 0

        pos = self.text_rect.move(
                self.rect.x + gap -offset[0],
                self.rect.y + (self.text_rect.h / 2) - (right_part_height/ 2) -offset[1],
            ).topright
        self.indicator.rect.topleft = pos

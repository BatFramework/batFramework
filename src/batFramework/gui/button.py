from .label import Label
import batFramework as bf
from typing import Self, Callable,Any
from .clickableWidget import ClickableWidget
import pygame
from math import ceil


class Button(Label, ClickableWidget):
    def __init__(self, text: str = "", callback: Callable[[],Any] = None) -> None:
        super().__init__(text=text)
        self.set_callback(callback)

    def __str__(self) -> str:
        return f"Button({self.text})"

    def get_min_required_size(self) -> tuple[float, float]:
        if not (self.autoresize_w or self.autoresize_h):
            return self.rect.size
        if not self.text_rect:
            self.text_rect.size = self._get_text_rect_required_size()
        res = self.inflate_rect_by_padding((0, 0, *self.text_rect.size)).size
        res = res[0],res[1]+self.unpressed_relief
        return res[0] if self.autoresize_w else self.rect.w, (
            res[1] if self.autoresize_h else self.rect.h
        )


    def _build_layout(self) -> None:

        self.text_rect.size = self._get_text_rect_required_size()
        if self.autoresize_h or self.autoresize_w:
            target_rect = self.inflate_rect_by_padding((0, 0, *self.text_rect.size))
            target_rect.h += self.unpressed_relief
            if not self.autoresize_w:
                target_rect.w = self.rect.w
            if not self.autoresize_h:
                target_rect.h = self.rect.h
            if self.rect.size != target_rect.size:
                self.set_size(target_rect.size)
                self.apply_updates()
                return
        offset = self._get_outline_offset() if self.show_text_outline else (0,0)
        padded = self.get_padded_rect().move(-self.rect.x + offset[0], -self.rect.y + offset[1])
        self.align_text(self.text_rect, padded, self.alignment)

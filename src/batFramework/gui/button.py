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

        res = self.inflate_rect_by_padding(
                    (0, 0, *self._get_text_rect_required_size())
                ).size
        res = res[0],res[1]+self.unpressed_relief
        return res[0] if self.autoresize_w else self.rect.w, (
            res[1] if self.autoresize_h else self.rect.h
        )


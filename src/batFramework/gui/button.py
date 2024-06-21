from .label import Label
import batFramework as bf
from typing import Self, Callable
from .clickableWidget import ClickableWidget
import pygame
from math import ceil


class Button(Label, ClickableWidget):
    def __init__(self, text: str, callback: None | Callable = None) -> None:
        super().__init__(text=text)
        self.set_callback(callback)
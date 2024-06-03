from .shape import Shape
from typing import Any, Self
import pygame
from .widget import Widget
from .interactiveWidget import InteractiveWidget
from .draggableWidget import DraggableWidget
import batFramework as bf


class Indicator(Shape):
    def __init__(self, size: tuple[int | float] = (10, 10)) -> None:
        super().__init__(size)
        self.debug_color = "magenta"
        self.set_outline_width(1)
        self.set_outline_color("black")

    def to_string_id(self) -> str:
        return "Indicator"

    def set_value(self, value: Any) -> None:
        pass

    def get_value(self) -> Any:
        pass


    def top_at(self, x, y):
        return None


class ToggleIndicator(Indicator):
    def __init__(self, default_value: bool) -> None:
        self.value: bool = default_value
        self.callback = lambda val : self.set_color("green" if val else "red")
        super().__init__((20, 20))
        self.set_value(default_value)

        # TODO aspect ratio would be good right about here
        # self.add_constraint(ConstraintAspectRatio(1))

    def set_callback(self, callback) -> Self:
        self.callback = callback
        return self

    def set_value(self, value: bool) -> None:
        self.value = value
        if self.callback:
            self.callback(value)
        self.dirty_surface = True

    def get_value(self) -> bool:
        return self.value

    def top_at(self, x: float, y: float) -> "None|Widget":
        r = super().top_at(x, y)
        if r is self:
            return None
        return r

        

from .shape import Shape
from .interactiveWidget import InteractiveWidget
from typing import Any
import pygame

# from .constraints import ConstraintAspectRatio


class Indicator(Shape,InteractiveWidget):
    def __init__(self, size : tuple[int | float] = (10,10)) -> None:
        super().__init__(size)

    def to_string_id(self) -> str:
        return "Indicator"

    def set_value(self, value: Any) -> None:
        pass

    def get_value(self) -> Any:
        pass

    def _build_indicator(self) -> None:
        pass

    def build(self) -> None:
        super().build()
        self._build_indicator()

    def top_at(self,x,y):return None


class ToggleIndicator(Indicator):
    def __init__(self, default_value: bool) -> None:
        self.value: bool = default_value
        super().__init__((20, 20))

        #TODO aspect ratio would be good right about here
        # self.add_constraint(ConstraintAspectRatio(1))

    def set_value(self, value) -> None:
        self.value = value
        self.set_color("green" if value else "red")
        self.build()

    def get_value(self) -> bool:
        return self.value

    def top_at(self, x: float, y: float) -> "None|Widget":
        return None

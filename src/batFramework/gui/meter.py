import math
import batFramework as bf
from .shape import Shape
from typing import Self


def custom_top_at(self, x, y):
    if Shape.top_at(self, x, y) == self:
        return self.parent
    return None

class Meter(Shape):
    def __init__(self, min_value: float = 0, max_value: float = 1, step: float = 0.1):
        super().__init__()
        self.min_value, self.max_value = min_value, max_value
        self.step = step
        self.snap: bool = False
        self.value = self.max_value
        self.set_debug_color("pink")

    def __str__(self) -> str:
        return "Meter"

    def set_step(self, step: float) -> Self:
        self.step = step
        self.set_value(self.value)
        return self

    def set_range(self, range_min: float, range_max: float) -> Self:
        if range_min >= range_max:
            return self
        self.min_value = range_min
        self.max_value = range_max
        self.dirty_shape = True

    def set_value(self, value: float) -> Self:
        value = max(self.min_value, min(self.max_value, value))
        value = round(value / self.step) * self.step
        self.value = round(value,10)
        self.dirty_shape = True
        return self

    def get_value(self) -> float:
        return self.value

    def get_range(self) -> float:
        return self.max_value - self.min_value

    def get_ratio(self) -> float:
        return (self.value-self.min_value) / (self.max_value - self.min_value)


class BarMeter(Meter):
    def __init__(self, min_value: float = 0, max_value: float = 1, step: float = 0.1):
        super().__init__(min_value, max_value, step)
        self.axis: bf.axis = bf.axis.HORIZONTAL
        self.content = Shape((0, 0)).set_color(bf.color.BLUE)
        self.content.set_debug_color("cyan")
        self.content.top_at = lambda x, y: custom_top_at(self.content, x, y)
        self.add(self.content)
        self.set_padding(4)
        self.set_color("gray20")
        self.set_outline_width(1)
        self.set_outline_color(bf.color.BLACK)
        self.set_debug_color("pink")

    def __str__(self) -> str:
        return "BarMeter"

    def set_axis(self,axis:bf.axis)->Self:
        self.axis = axis
        self.dirty_shape = True
        return self

    def _build_content(self) -> None:
        padded = self.get_inner_rect()
        ratio = self.get_ratio()

        self.content.set_border_radius(*[round(b/2) for b in self.border_radius])

        if self.axis == bf.axis.HORIZONTAL:
            width = (padded.width- self.outline_width *2) * ratio 
            self.content.set_size((width, padded.height - self.outline_width*2))
            self.content.rect.topleft = padded.move(self.outline_width, self.outline_width).topleft

        else:  # vertical
            height = (padded.height - self.outline_width * 2) * ratio
            self.content.set_size((padded.width - self.outline_width * 2, height))
            self.content.rect.bottomleft = (
                padded.move(self.outline_width,-self.outline_width).bottomleft 
            )
            self.content.rect.height = math.ceil(self.content.rect.height)

    def build(self) -> None:
        self._build_content()
        super().build()

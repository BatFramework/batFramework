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
        self.axis: bf.axis = bf.axis.HORIZONTAL
        self.min_value, self.max_value = min_value, max_value
        self.step = step
        self.snap: bool = False
        self.value = self.max_value
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
        return "Meter"

    def set_axis(self,axis:bf.axis)->Self:
        self.axis = axis
        self.dirty_shape = True
        return self

    def set_step(self, step: float) -> Self:
        self.step = step
        self.set_value(self.value)
        return self

    def set_range(self, range_min: float, range_max: float) -> Self:
        if range_min >= range_max:
            print(
                f"[Warning] : minimum value {range_min} is greater than or equal to maximum value {range_max}"
            )
            return self
        self.min_value = range_min
        self.max_value = range_max
        self.dirty_shape = True

    def get_debug_outlines(self):
        yield from super().get_debug_outlines()
        # yield from self.content.get_debug_outlines()

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

    def _build_content(self) -> None:
        padded = self.get_padded_rect()
        ratio = self.get_ratio()

        if self.axis == bf.axis.HORIZONTAL:
            width = padded.width * ratio
            self.content.set_size((width, padded.height))
            self.content.rect.topleft = padded.topleft

        else:  # VERTICAL
            height = padded.height * ratio
            self.content.set_size((padded.width, height))
            # Content grows from bottom up
            self.content.rect.bottomleft = padded.bottomleft


    def build(self) -> None:
        self._build_content()
        super().build()

import math
import batFramework as bf
from .shape import Shape
from typing import Self
from .syncedVar import SyncedVar

def custom_top_at(self, x, y):
    if Shape.top_at(self, x, y) == self:
        return self.parent
    return None

class Meter(Shape):
    def __init__(self, min_value: float = 0, max_value: float = None, step: float = 0.1, synced_var: SyncedVar = None):
        super().__init__()
        self.min_value, self.max_value = min_value, max_value
        self.step = step
        self.snap: bool = False
        self.synced_var = synced_var or SyncedVar(min_value)
        if self.max_value is None:
            self.max_value = self.synced_var.value
        self.synced_var.bind(self, self._on_synced_var_update)
        self.set_debug_color("pink")

    def __str__(self) -> str:
        return "Meter"

    def set_snap(self,snap:bool)->Self:
        self.snap = snap
        self.set_value(self.get_value())
        return self

    def set_step(self, step: float) -> Self:
        self.step = step
        self.set_value(self.get_value())
        return self

    def set_range(self, range_min: float, range_max: float) -> Self:
        if range_min >= range_max:
            return self
        self.min_value = range_min
        self.max_value = range_max
        self.dirty_shape = True
        return self

    def set_value(self, value: float) -> Self:
        """
        Sets the value of the meter and updates the synced variable.
        """
        value = max(self.min_value, min(self.max_value, value))
        value = round(value / self.step) * self.step
        value = round(value, 10)
        self.synced_var.value = value  # Update the synced variable
        return self

    def get_value(self) -> float:
        """
        Gets the current value from the synced variable.
        """
        return self.synced_var.value

    def get_range(self) -> float:
        return self.max_value - self.min_value

    def get_ratio(self) -> float:
        if self.max_value <= self.min_value:
            return 0
        return (self.get_value() - self.min_value) / (self.max_value - self.min_value)

    def _on_synced_var_update(self, value: float) -> None:
        """
        Updates the meter's internal state when the synced variable changes.
        """
        self.dirty_shape = True

    def set_synced_var(self, synced_var: SyncedVar) -> Self:
        """
        Rebinds the meter to a new SyncedVar.
        """
        if self.synced_var:
            self.synced_var.unbind(self)
        self.synced_var = synced_var
        self.synced_var.bind(self, self._on_synced_var_update)
        return self

class BarMeter(Meter):
    def __init__(self, min_value = 0, max_value = None, step = 0.1, synced_var = None):
        super().__init__(min_value, max_value, step, synced_var)
        self.axis: bf.axis = bf.axis.HORIZONTAL
        self.direction = bf.direction.RIGHT  # Direction determines which side is the max range
        self.content = Shape((4, 4)).set_color(bf.color.BLUE)
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

    def set_direction(self, direction: bf.direction) -> Self:
        """
        Sets the direction of the BarMeter.
        """
        self.direction = direction
        if self.axis == bf.axis.HORIZONTAL and self.direction in [bf.direction.UP, bf.direction.DOWN]:
            self.set_axis(bf.axis.VERTICAL)
        elif self.axis == bf.axis.VERTICAL and self.direction in [bf.direction.LEFT, bf.direction.RIGHT]:
            self.set_axis(bf.axis.HORIZONTAL)
        self.dirty_shape = True
        return self

    def set_axis(self,axis:bf.axis)->Self:
        self.axis = axis
        if axis==bf.axis.HORIZONTAL and self.direction not in [bf.direction.LEFT,bf.direction.RIGHT]:
            self.direction = bf.direction.RIGHT
        elif axis == bf.axis.VERTICAL and self.direction not in [bf.direction.UP, bf.direction.DOWN]:
            self.direction = bf.direction.UP

        self.dirty_shape = True
        return self

    def _build_content(self) -> None:
        padded = self.get_inner_rect()
        ratio = self.get_ratio()

        self.content.set_border_radius(*[round(b / 2) for b in self.border_radius])

        if self.axis == bf.axis.HORIZONTAL:
            width = (padded.width - self.outline_width * 2) * ratio
            width = max(width,0)
            self.content.set_size((width, padded.height - self.outline_width * 2))
            if self.direction == bf.direction.RIGHT:
                self.content.rect.topleft = padded.move(self.outline_width, self.outline_width).topleft
            else:  # bf.direction.LEFT
                self.content.rect.topright = padded.move(-self.outline_width, self.outline_width).topright

        else:  # vertical
            height = (padded.height - self.outline_width * 2) * ratio
            height = round(height)
            height = max(height,0)

            self.content.set_size((padded.width - self.outline_width * 2, height))
            if self.direction == bf.direction.UP:
                

                self.content.rect.bottomleft = (padded.left + self.outline_width, padded.bottom - self.outline_width)
            else:  # bf.direction.DOWN
                self.content.rect.topleft = padded.move(self.outline_width, self.outline_width).topleft

    def build(self) -> None:
        self._build_content()
        super().build()

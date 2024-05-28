from .shape import Shape
from typing import Any, Self
import pygame
from .widget import Widget
from .interactiveWidget import InteractiveWidget
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
        self.callback = None
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
class SliderHandle(Indicator, InteractiveWidget):
    def do_when_added(self):
        self.clicked_inside = False
        self.action = bf.Action("click").add_mouse_control(1).set_holding()

    def do_on_click_down(self, button: int) -> None:
        if self.parent : self.parent.get_focus()
        self.clicked_inside = True
        super().do_on_click_down(button)

    def do_process_actions(self, event: pygame.Event) -> None:
        self.action.process_event(event)

    def do_reset_actions(self) -> None:
        self.action.reset()

    def on_mouse_motion(self, x, y):
        if self.clicked_inside and self.action.is_active():
            centerx = x - self.parent.meter.get_padded_left() - self.rect.w // 2
            self.parent.set_value(
                (centerx / self.parent.get_meter_active_width())
                * self.parent.meter.get_range()
            )
            self.dirty_surface = True
        elif self.clicked_inside:
            self.clicked_inside = False

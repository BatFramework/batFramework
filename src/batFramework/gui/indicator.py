from __future__ import annotations
from .shape import Shape
from typing import Any, Self, Callable
import pygame
from .widget import Widget
from .interactiveWidget import InteractiveWidget
from .draggableWidget import DraggableWidget
import batFramework as bf


class Indicator(Shape):
    """
    Shape intended to be used as icons/indicators
    due to its nature, it overrides the top_at function (it can not be 'seen' by the mouse)
    
    """
    
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
        super().__init__((20, 20))
        self.value: bool = default_value
        self.on_color = bf.color.GREEN
        self.off_color= bf.color.RED
        self.callback = lambda val: self.set_color(self.on_color if val else self.off_color)
        self.set_value(default_value)
        self.callback(default_value)
        self.add_constraints(bf.gui.AspectRatio(1,reference_axis=bf.axis.VERTICAL))

    def set_off_color(self, color:pygame.typing.ColorLike):
        self.off_color = color
        self.dirty_surface = True

    def set_on_color(self, color:pygame.typing.ColorLike):
        self.on_color = color
        self.dirty_surface = True

    def __str__(self):
        return "ToggleIndicator"

    def set_callback(self, callback : Callable[[bool],Any]) -> Self:
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

class ArrowIndicator(Indicator):
    def __init__(self,direction:bf.direction):
        super().__init__()
        self.direction : bf.direction = direction
        self.arrow_color = bf.color.WHITE
        self.line_width : int = 1

    def set_arrow_color(self,color)-> Self:
        self.arrow_color = color
        self.dirty_surface = True
        return self

    def set_arrow_direction(self,direction:bf.direction)->Self:
        self.direction = direction
        self.dirty_surface = True
        return self

    def set_arrow_line_width(self,value:int)->Self:
        self.line_width = value
        self.dirty_surface = True
        return self
        
    def paint(self):
        super().paint()
        r = self.get_local_inner_rect()
        size = min(r.width, r.height)
        if size %2 == 0:
            size -= 1
        r.width = size
        r.height = size

        #pixel alignment
        if (self.padding[1]+self.padding[3] )%2 ==0:
            r.height-=1
        if (self.padding[0]+self.padding[2] )%2 ==0:
            r.width-=1
        r.center = self.get_local_inner_rect().center

        bf.utils.draw_triangle(
            surface = self.surface,
            color = self.arrow_color,
            rect =r,
            direction = self.direction,
            width = self.line_width

        )
        



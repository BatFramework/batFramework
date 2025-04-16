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
        self.callback = lambda val: self.set_color("green" if val else "red")
        self.set_value(default_value)
        self.callback(default_value)
        # TODO aspect ratio would be good right about here
        self.add_constraints(bf.gui.AspectRatio(1,reference_axis=bf.axis.VERTICAL))

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
        self.angle : float  = 45
        self.spread : float = None 
        self.draw_stem : bool = True
        
    def set_draw_stem(self,value:bool)->Self:
        self.draw_stem = value
        self.dirty_surface = False
        return self

    def set_spread(self,value:float)->Self:
        self.spread = value
        self.dirty_surface = True
        return self

    def set_angle(self,value:float)->Self:
        self.angle = value
        self.dirty_surface = True
        return self
        
    def set_arrow_color(self,color)-> Self:
        self.arrow_color = color
        self.dirty_surface = True
        return self

    def set_direction(self,direction:bf.direction)->Self:
        self.direction = direction
        self.dirty_surface = True
        return self

    def set_line_width(self,value:int)->Self:
        self.line_width = value
        self.dirty_surface = True
        return self
        
    def paint(self):
        super().paint()
        r = self.get_local_padded_rect()
        r.inflate_ip(-2,-2)
        r.normalize()
        # r.move_ip(-self.rect.left,-self.rect.right)
        bf.utils.draw_triangle(
            surface = self.surface,
            color = self.arrow_color,
            rect =r,
            direction = self.direction,
        )
        



import batFramework as bf
from .shape import Shape
from typing import Self
from math import ceil
class Meter(Shape):

    def __init__(self,size:tuple[float,float],min_value:float=0,max_value:float=1,step:float=0.1):
        if min_value > max_value:
            min_value = max_value
            print(f"[Warning] : minimum value {min_value} is greater than maximum value {max_value}")
        self.min_value, self.max_value = min_value,max_value
        self.step = step
        self.snap:bool=False
        self.value = max_value
        self.content = Shape((0,0))
        super().__init__(size)
        self.set_outline_width(1)
        self.set_outline_color(bf.color.BLACK)
    def get_bounding_box(self):
        yield from super().get_bounding_box()
        yield from self.content.get_bounding_box()

    def set_value(self,value:float)->Self:
        value = max(self.min_value,min(self.max_value,value))
        value = round(value/self.step) * self.step
        self.value = value
        self.build()
        return self


    def get_ratio(self)->float:
        return self.value / (self.max_value - self.min_value)

    def _build_content(self)->None:
        self.content.set_size((self.get_content_width() * self.get_ratio(),self.get_content_height()))
        self.content.set_position(*self.get_content_rect().topleft)
        
    def build(self)->None:
        super().build()
        self._build_content()
        self.surface.blit(self.content.surface,self.content.rect.move(-self.rect.x,-self.rect.y))

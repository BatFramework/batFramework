import batFramework as bf
from .shape import Shape
from typing import Self
from math import ceil
class Meter(Shape):

    def __init__(self):

        self.min_value, self.max_value = 0,1
        self.step = 0.1
        self.snap:bool=False
        self.value = self.max_value
        self.content = Shape((0,0))
        Shape.__init__(self,(100,30))
        self.set_outline_width(1)
        self.set_outline_color(bf.color.BLACK)
        self.content.set_outline_width(1)
        self.content.set_color(bf.color.BLACK)
        
    def set_range(self,min_val:float,max_val:float)->Self:
        self.max_value = max_val
        self.min_value = min_val
        self.set_value(self.value)
        return self

    def set_step(self,step:float)->Self:
        self.step = step
        self.set_value(self.value)
        return self        
    
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

import batFramework as bf
from .shape import Shape
from typing import Self

def custom_top_at(self,x,y):
    if (Shape.top_at(self,x,y) == self) : return self.parent
    return None
class Meter(Shape):
    
    def __init__(self,size:tuple[float,float],min_value:float=0,max_value:float=1,step:float=0.1):
        self.min_value, self.max_value = 0,1
        self.step = step
        self.snap:bool=False
        self.value = self.max_value
        self.content = Shape((0,0))
        self.content.top_at = lambda x,y: custom_top_at(self.content,x,y)
        super().__init__(size)
        self.add_child(self.content)
        self.set_outline_width(1)
        self.set_outline_color(bf.color.BLACK)
        self.set_debug_color("pink")
    
    def to_string_id(self) -> str:
        return "Meter"


    def set_step(self,step:float)->Self:
        self.step = step
        self.set_value(self.value)
        return self


    def set_range(self,range_min: float,range_max: float)->Self:
        if range_min >= range_max:
            print(f"[Warning] : minimum value {range_min} is greater than or equal to maximum value {range_max}")
            return self
        self.min_value,self.max_value = range_min,range_max
        self.build()

    def get_bounding_box(self):
        yield from super().get_bounding_box()
        yield from self.content.get_bounding_box()

    def set_value(self,value:float)->Self:
        value = max(self.min_value,min(self.max_value,value))
        value = round(value/self.step) * self.step
        self.value = value
        self.build()
        return self

    def get_value(self)->float:
        return self.value

    def get_range(self)->float:
        return self.max_value - self.min_value

    def get_ratio(self)->float:
        return self.value / (self.max_value - self.min_value)

    def _build_content(self)->None:
        self.content.set_size((self.get_padded_width() * self.get_ratio(),self.get_padded_height()))
        self.content.set_position(*self.get_padded_rect().topleft)
        
    def build(self)->None:
        super().build()
        self._build_content()
        self.surface.blit(self.content.surface,self.content.rect.move(-self.rect.x,-self.rect.y))

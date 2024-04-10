import batFramework as bf
from .meter import Meter
from .button import Button
from .interactiveWidget import InteractiveWidget
from .indicator import Indicator




class Slider(Meter,InteractiveWidget):

    def __init__(self,callback=None) -> None:
        self.value: float = 1
        self.gap: float | int = 0
        self.callback = callback
        self.indicator: Indicator = bf.Indicator((10,10)).add_constraints(bf.constraints.PercentageHeight(1.0))
        super().__init__()

        self.add_child(self.indicator)
        #self.indicator.


    def on_mouse_motion(self,x,y):
        internal_coord = (x-self.rect.x,y-self.rect.y)
        print(internal_coord)
        if self.is_clicked_down:
            val = internal_coord[0] / self.get_content_width()
            self.set_value(val)
            if self.callback : self.callback(self.value)


    def build(self)->None:
        super().build()
        self.indicator.set_center(*self.get_content_rect().move(self.content.get_content_width(),0).midleft)

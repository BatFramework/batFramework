import batFramework as bf
from .button import Button
from .indicator import ToggleIndicator

class Slider(Button):
    def __init__(self, text: str, default_value: float = 1.0 ,callback=None) -> None:
        self.value: float = min(1.0,max(0.0,default_value))
        self.indicator: Indicator = bf.Shape(0,0)
        self.gap: float | int = 0
        super().__init__(text, callback)
        self.add_child(self.indicator)


    def click(self) -> None:
        if self.callback is not None:
            self.set_value(not self.value,True)
            bf.Timer(duration=0.3,end_callback=self._safety_effect_end).start()

    def on_mouse_motion(self,x,y):
        self.build()
        self.surface.fill("red",(x-self.rect.x,y-self.rect.y,2,2))

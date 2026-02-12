from .label import Label
import batFramework as bf
import sys

class ToolTip(Label):
    def __init__(self, text = ""):
        super().__init__(text)
        self.fade_in_duration : float = 0.1
        self.fade_out_duration : float = 0.1
        self.set_render_order(sys.maxsize)
        self.set_padding(2)
    
    def __str__(self):
        return f"ToolTip('{self.text_widget.text}')"

    def top_at(self, x, y):
        return None

    def set_all_alpha(self,value:int):
        self.text_widget.set_alpha(value)
        return self.set_alpha(value)

    def fade_in(self):
        self.set_visible(True)
        bf.PropertyEaser(
            self.fade_in_duration,bf.easing.EASE_OUT,
            0,self.parent_scene.name
        ).add_custom(self.get_alpha,self.set_all_alpha,255).start()

    def fade_out(self):
        bf.PropertyEaser(
            self.fade_out_duration,bf.easing.EASE_IN,
            0,self.parent_scene.name,
            lambda : self.set_visible(False)
        ).add_custom(self.get_alpha,self.set_all_alpha,0).start()

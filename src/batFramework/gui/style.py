from .widget import Widget
import batFramework as bf
from .shape import Shape
from .label import Label
from .textInput import TextInput
class Style:

    def __init__(self):
        pass

    def apply(self, widget: Widget):
        pass



class DefaultStyle(Style):
    def apply(self, w):
        if isinstance(w,Shape):
            w.set_color(bf.color.WHITE)
            w.set_outline_width(1)
            w.set_outline_color(bf.color.DARK_GRAY)
            w.set_shadow_color(bf.color.CLOUD_SHADE)
            w.set_padding(4)
        if isinstance(w, Label):
            w.set_text_bg_color(bf.color.WHITE)
            w.set_text_color(bf.color.CHARCOAL_SHADE)
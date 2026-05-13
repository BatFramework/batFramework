from .widget import Widget
import batFramework as bf
from .shape import Shape
from .label import Label
from .textInput import TextInput
from .clickableWidget import ClickableWidget
from .indicator import Indicator
from .container import Container


class Style:

    def __init__(self):
        pass

    def init(self):
        """
        Safe to call when resources are loaded
        """

    def apply(self, widget: Widget):
        pass


class DefaultStyle(Style):
    def apply(self, w):
        if isinstance(w, Shape):
            
            w.set_color(bf.color.CREAM)
            w.set_outline_width(1)
            w.set_outline_color(bf.color.DARK_GRAY)
            w.set_shadow_color(bf.color.CLOUD_SHADE)
        if isinstance(w, Label):
            w.set_text_bg_color(bf.color.WHITE)
            w.set_text_color(bf.color.BLACK)
        if isinstance(w,ClickableWidget):
            w.set_unpressed_relief(0)
            w.set_pressed_relief(0)
            
        if isinstance(w,Container):
            w.set_padding(4)    
import batFramework as bf
from .widget import Widget
from .layout import Layout
from .constraints import Constraint


class Container(Widget):
    def __init__(self, layout:Layout=None, *children:Widget):
        super().__init__()
        self.surface = None
        for child in children:
            self.add_child(child)

        self.layout :Layout = layout
        if self.layout : self.layout.set_parent(self)


    def add_child(self,*children:Widget)->None:
        super().add_child(*children)
        if self.layout : self.layout.arrange()


    def to_string(self)->str:
        return f"Container@{*self.rect.topleft,* self.rect.size}"


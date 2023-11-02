import batFramework as bf
from .widget import Widget
from .layout import Layout
from .constraints import Constraint
from typing import Self

class Container(Widget):
    def __init__(self, layout:Layout=None, *children:Widget):
        super().__init__()
        self.surface = None
        self.layout :Layout = layout
        if self.layout : self.layout.set_parent(self)
        for child in children:
            self.add_child(child)

    def set_parent(self,parent:Widget)->Self:
        super().set_parent(parent) # Calls apply_constraints()
        return self

    def get_bounding_box(self):
        r = (self.rect,self._debug_color)
        yield r
        for child in self.children:
            yield from child.get_bounding_box()


    def clear_children(self)->None:
        self.children.clear()
        if self.layout : self.layout.arrange()

    def remove_child(self,child:Widget)->None:
        super().remove_child(child)
        if self.layout : self.layout.arrange()

    def add_child(self,*children:Widget)->None:
        super().add_child(*children)
        if self.layout : self.layout.arrange()

    def build(self)->None:
        super().build()
        if self.layout : self.layout.arrange()

    def apply_constraints(self)->None:
        if self.layout : self.layout.arrange()
        super().apply_constraints()

    def to_string_id(self)->str:
        return f"Container({len(self.children)},{[c.to_string() for c in self.constraints]})"

    def children_modified(self):
        if self.layout : self.layout.arrange()
        super().apply_constraints()
        super().children_modified()

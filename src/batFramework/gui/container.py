import batFramework as bf
from .widget import Widget
from .layout import Layout,Column
from .constraints import Constraint
from typing import Self

class Container(Widget):
    def __init__(self, layout: Layout = Column(), *children: Widget)->None:
        super().__init__()
        self.set_debug_color("green")
        self.surface = None
        self.layout: Layout = layout
        if self.layout:
            self.layout.set_parent(self)
        for child in children:
            self.add_child(child)

    def set_layout(self, layout: Layout) -> Self:
        self.layout = layout
        self.apply_constraints()
        return self

    def get_bounding_box(self):
        yield (self.rect, self.debug_color)
        for child in self.children:
            yield from child.get_bounding_box()

    def clear_children(self) -> None:
        self.children.clear()
        self.apply_constraints()

    def add_child(self, *child: Widget) -> None:
        super().add_child(*child)
        if self.layout:
            self.layout.arrange()

    def remove_child(self, child: Widget) -> None:
        super().remove_child(child)
        if self.layout:
            self.layout.arrange()

    def build(self) -> None:
        super().build()
        if self.layout:
            self.layout.arrange()

    def apply_constraints(self) -> None:
        super().apply_constraints()
        if self.layout:
            self.layout.arrange()

    def to_string_id(self) -> str:
        return f"Container({self.uid},{len(self.children)},{[c.to_string() for c in self.constraints]})"

    def children_modified(self)->None:
        self.apply_all_constraints()
        super().children_modified()

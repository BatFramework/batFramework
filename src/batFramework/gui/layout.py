import batFramework as bf
from .widget import Widget
from .constraints.constraints import *
from typing import Self,TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from .container import Container

class Layout:
    def __init__(self, parent: "Container" = None):
        self.parent = parent
        self.child_constraints: list[Constraint] = []
        self.children_rect = pygame.FRect(0, 0, 0, 0)

    def set_child_constraints(self, *constraints) -> Self:
        self.child_constraints = list(constraints)
        self.notify_parent()
        return self

    def set_parent(self, parent: Widget):
        self.parent = parent
        self.notify_parent()

    def notify_parent(self) -> None:
        if self.parent:self.parent.dirty_children = True

    def arrange(self) -> None:
        raise NotImplementedError("Subclasses must implement arrange method")


    def get_fit_size(self)->tuple[float,float]:
        return 0,0

class Column(Layout):
    def __init__(self, gap: int = 0):
        super().__init__()
        self.gap = gap

    def set_gap(self, value: float) -> Self:
        self.gap = value
        self.notify_parent()
        return self

    def get_fit_size(self):
        len_children = len(self.parent.children)

        parent_height = sum(c.get_min_required_size()[1] for c in self.parent.children)
        parent_width = max(c.get_min_required_size()[0] for c in self.parent.children)
        if self.gap:
            parent_height += (len_children - 1) * self.gap

        target_rect = self.parent.inflate_rect_by_padding((0,0,parent_width,parent_height))
        return target_rect.size
        
    def arrange(self) -> None:
        if not self.parent or not self.parent.children:
            return
        if self.child_constraints :  
            for child in self.parent.children : child.add_constraints(*self.child_constraints)
              
        self.child_rect = self.parent.get_padded_rect()

        if self.parent.fit_to_children:
            width,height = self.get_fit_size()
            if self.parent.rect.size != (width,height):
                self.parent.set_size((width,height))
                self.parent.build()
                self.arrange()
                return

        y = self.child_rect.top
        for child in self.parent.children :
            child.set_position(self.child_rect.x,y)
            y+= child.get_min_required_size()[1] + self.gap

class Row(Layout):
    def __init__(self, gap: int = 0):
        super().__init__()
        self.gap = gap

    def set_gap(self, value: float) -> Self:
        self.gap = value
        self.notify_parent()
        return self

    def get_fit_size(self):
        len_children = len(self.parent.children)

        parent_width = sum(c.get_min_required_size()[0] for c in self.parent.children)
        parent_height = max(c.get_min_required_size()[1] for c in self.parent.children)

        if self.gap:
            parent_width += (len_children - 1) * self.gap

        target_rect = self.parent.inflate_rect_by_padding((0, 0, parent_width, parent_height))
        return target_rect.size

    def arrange(self) -> None:
        if not self.parent or not self.parent.children:
            return
        if self.child_constraints:
            for child in self.parent.children:
                child.add_constraints(*self.child_constraints)

        self.child_rect = self.parent.get_padded_rect()

        if self.parent.fit_to_children:
            width, height = self.get_fit_size()
            if self.parent.rect.size != (width, height):
                self.parent.set_size((width, height))
                self.parent.build()
                self.arrange()
                return

        x = self.child_rect.left
        for child in self.parent.children:
            child.set_position(x, self.child_rect.y)
            x += child.get_min_required_size()[0] + self.gap

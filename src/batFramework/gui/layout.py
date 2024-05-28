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


class Column(Layout):
    def __init__(self, gap: int = 0):
        super().__init__()
        self.gap = gap

    def set_gap(self, value: float) -> Self:
        self.gap = value
        self.notify_parent()
        return self

    def arrange(self) -> None:
        if not self.parent or not self.parent.children:
            return
        
        # print(self.parent,"arranging",self.gap)
        self.child_rect = self.parent.get_padded_rect()
        len_children = len(self.parent.children)
        if self.parent.fit_to_children:
            parent_height = sum(c.get_min_required_size()[1] for c in self.parent.children)
            parent_width = max(c.get_min_required_size()[0] for c in self.parent.children)
            if self.gap:
                parent_height += (len_children - 1) * self.gap
            self.children_rect.update(
                *self.child_rect.topleft,
                parent_width,
                parent_height,
            )

        y = self.child_rect.top
        for child in self.parent.children :
            child.set_position(self.child_rect.x,y)
            y+= child.get_min_required_size()[1] + self.gap
            if self.child_constraints : child.add_constraints(*self.child_constraints)


class Row(Layout):
    def __init__(self, gap: int = 0, fit_children: bool = True, center: bool = True):
        super().__init__()
        self.gap = gap
        self.fit_children: bool = fit_children
        self.center = center

    def set_gap(self, value: float) -> Self:
        self.gap = value
        self.notify_parent()
        return self

    def arrange(self) -> None:
        if not self.parent or not self.parent.children:
            return
        len_children = len(self.parent.children)
        parent_width = sum(c.get_min_required_size()[0] for c in self.parent.children)
        parent_height = max(c.get_min_required_size()[1] for c in self.parent.children)

        if self.gap:
            parent_width += (len_children - 1) * self.gap
        self.children_rect.update(
            self.parent.get_padded_left(),
            self.parent.get_padded_top(),
            parent_width,
            parent_height,
        )
        if self.center:
            self.children_rect.center = self.parent.get_padded_center()
        if self.fit_children:
            self.parent.set_size((parent_width, parent_height))

        current_x = self.children_rect.left

        for child in self.parent.children:
            child.set_position(current_x, self.parent.rect.y)
            current_x += child.rect.w + self.gap
            for c in self.child_constraints:
                child.add_constraints(c)

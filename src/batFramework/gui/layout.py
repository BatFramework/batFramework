import batFramework as bf
from .widget import Widget
from .constraints import *
from typing import Self
import pygame


class Layout:
    def __init__(self, parent: Widget = None):
        self.parent = parent
        self.child_constraints: list[Constraint] = []
        self.children_rect = pygame.FRect(0, 0, 0, 0)

    def set_child_constraints(self, *constraints) -> Self:
        self.child_constraints = constraints
        self.arrange()
        return self

    def set_parent(self, parent: Widget):
        self.parent = parent
        self.arrange()

    def arrange(self) -> None:
        raise NotImplementedError("Subclasses must implement arrange  method")


class Column(Layout):
    def __init__(self, gap: int = 0, fit_children: bool = False, center: bool = False):
        super().__init__()
        self.gap = gap
        self.fit_children: bool = fit_children
        self.center = center

    def arrange(self) -> None:
        if not self.parent or not self.parent.children:
            return
        len_children = len(self.parent.children)
        parent_height = sum(c.get_min_required_size()[1] for c in self.parent.children)
        parent_width = max(c.get_min_required_size()[0] for c in self.parent.children)
        if self.gap:
            parent_height += (len_children - 1) * self.gap
        self.children_rect.update(
            self.parent.get_content_left(),
            self.parent.get_content_top(),
            parent_width,
            parent_height,
        )
        if self.center:
            self.children_rect.center = self.parent.rect.center
        if self.fit_children:
            self.parent.set_size(parent_width,parent_height)

        current_y = self.children_rect.top

        for child in self.parent.children:
            child.set_position(self.parent.rect.x, current_y)
            current_y += child.rect.h + self.gap
            for c in self.child_constraints:
                child.add_constraints(c)
                # if not child.has_constraint(c.name):


class Row(Layout):
    def __init__(self, gap: int = 0, fit_children: bool = False, center: bool = False):
        super().__init__()
        self.gap = gap
        self.fit_children: bool = fit_children
        self.center = center

    def arrange(self) -> None:
        if not self.parent or not self.parent.children:
            return

        len_children = len(self.parent.children)
        parent_width = sum(c.rect.w for c in self.parent.children)
        parent_height = max(c.rect.h for c in self.parent.children)
        if self.gap:
            parent_width += (len_children - 1) * self.gap
        self.children_rect.update(
            self.parent.get_content_left(),
            self.parent.get_content_top(),
            parent_width,
            parent_height,
        )
        if self.center:
            self.children_rect.center = self.parent.get_content_center()
        if self.fit_children:
            # c = self.parent.get_constraint("width")
            # if not c or c.width != parent_width:
            #     self.parent.add_constraints(ConstraintWidth(parent_width))
            # c = self.parent.get_constraint("height")
            # if not c or c.height != parent_height:
            #     self.parent.add_constraints(ConstraintHeight(parent_height))
            self.parent.set_size(parent_width,parent_height)
        current_x = self.children_rect.left

        for child in self.parent.children:
            child.set_position(current_x, self.parent.rect.y)
            current_x += child.rect.w + self.gap
            for c in self.child_constraints:
                if not child.has_constraint(c.name):
                    child.add_constraints(c)

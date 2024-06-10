import batFramework as bf
from .widget import Widget
from .shape import Shape
from .interactiveWidget import InteractiveWidget
from .layout import Layout, Column
from typing import Self
import pygame
from pygame.math import Vector2


class Container(Shape, InteractiveWidget):
    def __init__(self, layout: Layout = None, *children: Widget) -> None:
        super().__init__()
        self.dirty_children = False
        self.set_debug_color("green")
        self.layout: Layout = layout
        self.scroll = Vector2(0, 0)
        if not self.layout:
            self.layout = Column()
        self.layout.set_parent(self)
        self.add(*children)

    def get_min_required_size(self):
        if self.layout:
            return self.layout.get_auto_size()
        return self.rect.size

    def reset_scroll(self) -> Self:
        self.scroll.update(0, 0)
        self.dirty_children = True
        return self

    def set_scroll(self, value: tuple) -> Self:
        self.scroll.update(value)
        self.dirty_children = True
        return self

    def scrollX_by(self, x: float | int) -> Self:
        self.scroll.x += x
        self.dirty_children = True
        return self

    def scrollY_by(self, y: float | int) -> Self:
        self.scroll.y += y
        self.dirty_children = True
        return self

    def scroll_by(self, value: tuple[float | int, float | int]) -> Self:
        self.scroll += value
        self.dirty_children = True
        return self

    def set_layout(self, layout: Layout) -> Self:
        tmp = self.layout
        self.layout = layout
        if self.layout != tmp:
            self.dirty_children = True
        return self


    def get_debug_outlines(self):
        yield (self.rect, self.debug_color)
        yield (self.get_padded_rect(), self.debug_color)

        for child in self.children:
            yield from child.get_debug_outlines()
            # for data in child.get_debug_outlines():

    def get_interactive_children(self) -> list[InteractiveWidget]:
        return [
            child for child in self.children if isinstance(child, InteractiveWidget) and child.allow_focus_to_self()
        ]

    def focus_next_child(self) -> None:
        self.layout.focus_next_child()
        
    def focus_prev_child(self) -> None:
        self.layout.focus_prev_child()

    def clear_children(self) -> None:
        self.children.clear()
        self.dirty_children = True

    def add(self, *child: Widget) -> Self:
        super().add(*child)
        self.dirty_children = True
        return self

    def remove(self, *child: Widget) -> Self:
        super().remove(*child)
        self.dirty_children = True
        return self

    def resolve_constraints(self) -> None:
        super().resolve_constraints()

    def __str__(self) -> str:
        return f"Container({self.uid},{len(self.children)})"

    def top_at(self, x: float | int, y: float | int) -> "None|Widget":
        if self.visible and self.rect.collidepoint(x, y):
            if self.children:
                for child in reversed(self.children):
                    r = child.top_at(x,y)
                    if r is not None:
                        return r
            return self
        return None

    def get_focus(self) -> bool:
        res = super().get_focus()
        if not res:
            return False
        l = l = self.get_interactive_children()
        if not l:
            return True
        self.focused_index = min(self.focused_index, len(l))
        return l[self.focused_index].get_focus()

    def set_focused_child(self, child: InteractiveWidget) -> bool:
        l = self.get_interactive_children()
        i = l.index(child)
        if i >= 0:
            self.focused_index = i
            return True
        return False

    def allow_focus_to_self(self) -> bool:
        return len(self.get_interactive_children()) != 0

    def draw(self, camera: bf.Camera) -> None:
        constraints_down = False
        if self.dirty_shape:
            self.dirty_constraints = True
            self.dirty_children = True
            self.dirty_surface = True
            self.build()
            for child in self.children:
                child.dirty_constraints = True
            self.dirty_shape = False

        if self.dirty_constraints:
            if self.parent and self.parent.dirty_constraints:
                self.parent.visit_up(self.selective_up)
            else:
                constraints_down = True

        if self.dirty_children:
            if self.layout:
                self.layout.arrange()
            self.dirty_children = False

        if constraints_down:
            self.visit(lambda c: c.resolve_constraints())

        if self.dirty_surface:
            self.paint()
            self.dirty_surface = False


        bf.Entity.draw(self, camera)

        if self.clip_children:
            new_clip = camera.world_to_screen(self.get_padded_rect())
            old_clip = camera.surface.get_clip()
            new_clip = new_clip.clip(old_clip)
            camera.surface.set_clip(new_clip)
        # Draw children with adjusted positions
        _ = [child.draw(camera) for child in sorted(self.children, key=lambda c: c.render_order)]

        if self.clip_children:
            camera.surface.set_clip(old_clip)


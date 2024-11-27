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
        self.dirty_layout: bool = False
        self.set_debug_color("green")
        self.layout = layout if layout else Column()
        self.layout.set_parent(self)
        self.scroll = Vector2(0, 0)
        self.add(*children)

    def __str__(self) -> str:
        return f"Container({self.uid},{len(self.children)})"

    def get_min_required_size(self):
        return self.layout.get_auto_size() if self.layout else self.rect.size

    def reset_scroll(self) -> Self:
        if self.scroll == (0,0):
            return self
        self.scroll.update(0, 0)
        self.dirty_layout = True
        return self

    def set_scroll(self, value: tuple) -> Self:
        if (self.scroll.x,self.scroll.y) == value:
            return self
        self.scroll.update(value)
        self.clamp_scroll()
        self.dirty_layout = True
        return self

    def scrollX_by(self, x: float | int) -> Self:
        if x == 0:
            return self
        self.scroll.x += x
        self.clamp_scroll()
        self.dirty_layout = True
        return self

    def scrollY_by(self, y: float | int) -> Self:
        if y == 0:
            return self
        self.scroll.y += y
        self.clamp_scroll()
        self.dirty_layout = True
        return self

    def scroll_by(self, value: tuple[float | int, float | int]) -> Self:
        if value[0] == 0 and value[1] == 0:
            return self
        self.scroll += value
        self.clamp_scroll()
        self.dirty_layout = True
        return self

    def clamp_scroll(self) -> Self:
        if not self.children:
            return self
        r = self.get_padded_rect()
        size = self.children[0].rect.unionall([child.rect for child in self.children[1:]]).size

        max_scroll_x = max(0, size[0] - r.width)
        max_scroll_y = max(0, size[1] - r.height)

        self.scroll.x = max(0, min(self.scroll.x, max_scroll_x))
        self.scroll.y = max(0, min(self.scroll.y, max_scroll_y))
        self.dirty_layout = True
        return self

    def set_layout(self, layout: Layout) -> Self:
        tmp = self.layout
        self.layout = layout
        if self.layout != tmp:
            tmp.set_parent(None)
            self.layout.set_parent(self)
            self.dirty_layout = True
        return self

    def get_interactive_children(self) -> list[InteractiveWidget]:
        return [child for child in self.children if isinstance(child, InteractiveWidget) and not isinstance(child,Container) and child.allow_focus_to_self()]

    def clear_children(self) -> None:
        self.children.clear()
        self.dirty_layout = True

    def add(self, *child: Widget) -> Self:
        super().add(*child)
        self.dirty_shape = True
        self.clamp_scroll()
        return self

    def remove(self, *child: Widget) -> Self:
        super().remove(*child)
        self.dirty_shape = True
        self.clamp_scroll()
        return self

    def top_at(self, x: float | int, y: float | int) -> "None|Widget":
        if self.rect.collidepoint(x, y):
            for child in reversed(self.children):
                result = child.top_at(x, y)
                if result is not None:
                    return result
            return self
        return None

    def get_focus(self) -> bool:
        if not super().get_focus():
            return False
        interactive_children = self.get_interactive_children()
        if not interactive_children:
            return True
        self.focused_index = min(self.focused_index, len(interactive_children) - 1)
        return interactive_children[self.focused_index].get_focus()

    def do_handle_event(self, event) -> None:
        if any(child.is_focused for child in self.get_interactive_children()):
            self.layout.handle_event(event)

    def set_focused_child(self, child: InteractiveWidget) -> bool:
        interactive_children = self.get_interactive_children()
        try:
            index = interactive_children.index(child)
            self.focused_index = index
            return True
        except ValueError:
            return False

    def allow_focus_to_self(self) -> bool:
        return bool(self.get_interactive_children()) and self.visible


    def apply_updates(self):
        if any(child.dirty_shape for child in self.children):
            self.dirty_layout = True  # Mark layout as dirty if any child changed size

        if self.dirty_constraints:
            self.resolve_constraints()  # Finalize positioning based on size
    
        # Step 1: Build shape if needed
        if self.dirty_shape:
            self.build()  # Finalize size of the container
            self.dirty_shape = False
            self.dirty_surface = True  # Mark surface for repaint
            self.dirty_layout = True  # Mark layout for arrangement
            # Flag all children to update constraints after size is finalized
            for child in self.children:
                child.dirty_constraints = True

        for child in self.children:
            child.apply_updates()

        # Step 2: Arrange layout if marked as dirty
        if self.dirty_layout:
            self.layout.arrange()
            self.dirty_surface = True
            self.dirty_layout = False
            # Constraints may need to adjust based on the layout change
            self.dirty_constraints = True

        # Step 3: Resolve constraints now that size and layout are finalized
        if self.dirty_constraints:
            self.resolve_constraints()  # Finalize positioning based on size
            for child in self.children:
                child.dirty_constraints = True  # Children inherit updated positioning
            self.dirty_constraints = False

        # Step 4: Paint the surface if marked as dirty
        if self.dirty_surface:
            # print("PAINT !!")
            self.paint()
            self.dirty_surface = False

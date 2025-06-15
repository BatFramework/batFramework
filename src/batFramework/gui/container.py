import pygame
import batFramework as bf
from .widget import Widget
from .shape import Shape
from .interactiveWidget import InteractiveWidget
from .layout import Layout, Column
from typing import Self
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
        self.set_scroll((self.scroll.x + x, self.scroll.y))
        return self

    def scrollY_by(self, y: float | int) -> Self:
        if y == 0:
            return self
        self.set_scroll((self.scroll.x, self.scroll.y + y))
        return self

    def scroll_by(self, value: tuple[float | int, float | int]) -> Self:
        if value[0] == 0 and value[1] == 0:
            return self
        self.set_scroll((self.scroll.x + value[0], self.scroll.y + value[1]))
        return self

    def clamp_scroll(self) -> Self:
        if not self.children:
            return self
        r = self.get_inner_rect()
        # Compute the bounding rect of all children in one go
        children_rect = self.children[0].rect.copy()
        for child in self.children[1:]:
            children_rect.union_ip(child.rect)
        max_scroll_x = max(0, children_rect.width - r.width)
        max_scroll_y = max(0, children_rect.height - r.height)

        # Clamp scroll values only if needed
        new_x = min(max(self.scroll.x, 0), max_scroll_x)
        new_y = min(max(self.scroll.y, 0), max_scroll_y)

        self.set_scroll((new_x, new_y))
        return self

    def set_layout(self, layout: Layout) -> Self:
        tmp = self.layout
        self.layout = layout
        if self.layout != tmp:
            tmp.set_parent(None)
            self.layout.set_parent(self)
            self.reset_scroll()
            self.dirty_layout = True
        return self

    def get_interactive_children(self) -> list[InteractiveWidget]:
        return [child for child in self.get_layout_children() if isinstance(child, InteractiveWidget) and not isinstance(child,Container) and child.allow_focus_to_self()]

    def get_layout_children(self)->list[Widget]:
        return self.children

    def clear_children(self) -> None:
        self.children.clear()
        self.dirty_layout = True

    def add(self, *child: Widget) -> Self:
        super().add(*child)
        self.dirty_shape = True
        self.dirty_layout = True
        return self

    def remove(self, *child: Widget) -> Self:
        super().remove(*child)
        self.dirty_shape = True
        self.dirty_layout = True
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

    def children_has_focus(self)->bool:
        return any(child.is_focused for child in self.get_interactive_children())

    def do_handle_event(self, event) -> None:
        super().do_handle_event(event)
        if event.type == pygame.MOUSEWHEEL:
            # Adjust scroll based on the mouse wheel movement
            scroll_speed = 20  # Adjust this value to control the scroll speed
            self.scroll_by((0, -event.y * scroll_speed))  # Scroll vertically
            event.consumed = True  # Mark the event as consumed
        self.layout.handle_event(event)

    def set_focused_child(self, child: InteractiveWidget) -> bool:
        interactive_children = self.get_interactive_children()
        try:
            index = interactive_children.index(child)
            self.focused_index = index
            if self.layout : 
                self.layout.scroll_to_widget(child)
            return True
        except ValueError:
            return False

    def allow_focus_to_self(self) -> bool:
        return bool(self.get_interactive_children()) and self.visible
    
    def build(self) -> None:
        if self.layout is not None:
            # print("I'm building !",self)
            # size = self.expand_rect_with_padding((0,0,*self.layout.get_auto_size())).size
            size = self.layout.get_auto_size()
            self.set_size(self.resolve_size(size))
        super().build()

    def apply_pre_updates(self):
        if self.dirty_size_constraints or self.dirty_shape:
            self.resolve_constraints(size_only=True)
            self.dirty_size_constraints = False
            self.dirty_position_constraints = True

        if self.dirty_layout:
            self.layout.update_child_constraints()
            self.layout.arrange()
            self.dirty_layout = False

    def apply_post_updates(self,skip_draw:bool=False):
        """
        BOTTOM TO TOP
        for cases when widget attributes depend on children attributes
        """
        if self.dirty_shape:
            self.layout.update_child_constraints()
            self.build()
            self.dirty_shape = False
            self.dirty_surface = True
            self.dirty_layout =  True
            self.dirty_size_constraints = True
            self.dirty_position_constraints = True
            from .container import Container
            if self.parent and isinstance(self.parent, Container):
                self.parent.dirty_layout = True
                self.parent.dirty_shape = True

            # trigger layout or constraint updates in parent
            

            # force recheck of constraints


        if self.dirty_position_constraints:
            self.resolve_constraints(position_only=True)
            self.dirty_position_constraints= False


        if self.dirty_surface and not skip_draw:
            self.paint()
            self.dirty_surface = False



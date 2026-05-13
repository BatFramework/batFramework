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
        self.layout = layout if layout else Column()
        self.layout.set_parent(self)
        self.scroll = Vector2(0, 0)
        self.dirty_scroll = False
        self.set_debug_color("green")
        self.add(*children)

    def __str__(self) -> str:
        return f"Container({self.uid},{len(self.children)})"

    def get_min_required_size(self):
        if not self.layout:
            return self.rect.size
        return self.expand_rect_with_padding((0,0,*self.layout.get_auto_size())).size

    def reset_scroll(self) -> Self:
        if self.scroll == (0, 0):
            return self
        self.set_scroll((0, 0))
        return self

    def set_scroll(self, value: tuple[float]) -> Self:
        # print("Trying to set scroll to ",value)
        # print("Current scroll is : ",self.scroll)

        if (self.scroll.x, self.scroll.y) == value:
            return self
        self.scroll.update(value)
        # print("Scroll updated to", value)
        self.clamp_scroll()
        self.dirty_scroll = True
        # self.dirty_layout = True
        return self

    def scrollX_by(self, x: float) -> Self:
        if x == 0:
            return self
        self.set_scroll((self.scroll.x + x, self.scroll.y))
        return self

    def scrollY_by(self, y: float) -> Self:
        if y == 0:
            return self
        self.set_scroll((self.scroll.x, self.scroll.y + y))
        return self

    def scroll_by(self, value: tuple[float]) -> Self:
        self.set_scroll((self.scroll.x + value[0], self.scroll.y + value[1]))
        return self
    
    def clamp_scroll(self) -> Self:
        if not self.children:
            return self

        r = self.get_inner_rect()

        content_w = self.layout.children_rect.width
        content_h = self.layout.children_rect.height

        max_scroll_x = max(0, content_w - r.width)
        max_scroll_y = max(0, content_h - r.height)

        self.scroll.x = max(0, min(self.scroll.x, max_scroll_x))
        self.scroll.y = max(0, min(self.scroll.y, max_scroll_y))

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
        """Return all children that can be cycled through with focus"""
        return [
            child
            for child in self.get_layout_children()
            if isinstance(child, InteractiveWidget)
            and not isinstance(child, Container)
            and child.allow_focus_to_self()
        ]

    def get_layout_children(self) -> list[Widget]:
        """Returns all children affected by layout"""
        return self.children

    def clear_children(self) -> None:
        for child in self.children:
            child.set_parent(None)
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
        r = self.rect if not  self.clip_children else self.get_inner_rect()
        if r.collidepoint(x, y):
            for child in reversed(self.children):
                result = child.top_at(x, y)
                if result is not None:
                    return result
            if self.rect.collidepoint(x,y) : return self
        return None

    def on_get_focus(self, focus_area : pygame.Rect=None):
        interactive_children = self.get_interactive_children()
        if not interactive_children:
            return True
        self.focused_index = min(self.focused_index, len(interactive_children) - 1)
        return interactive_children[self.focused_index].ask_focus()


    def children_has_focus(self) -> bool:
        """Return true if any direct children is focused"""
        return any(child.is_focused for child in self.get_interactive_children())

    def handle_event(self, event) -> None:
        super().handle_event(event)
        self.layout.handle_event(event)

    def set_focused_child(self, child: InteractiveWidget, focus_area:pygame.Rect=None) -> bool:
        interactive_children = self.get_interactive_children()
        try:
            index = interactive_children.index(child)
            self.focused_index = index
            if self.layout:
                self.layout.scroll_to_widget(child,focus_area)
            return True
        except ValueError:
            return False

    def allow_focus_to_self(self) -> bool:
        """Return whether the container can get focused"""
        return bool(self.get_interactive_children()) and self.visible

    def build(self) -> None:
        if self.layout is not None:
            size = self.layout.get_auto_size()
            self.set_size(self.resolve_size(size))
        super().build()



    def apply_post_updates(self, skip_draw: bool = False) -> None:
        # ── 1. Resolve own size (same as Widget, inlined so we control flow) ──
        if self.dirty_shape:
            if self.build():
                # Our size changed — layout must re-run regardless of dirty_layout
                self.dirty_layout = True
                self.dirty_size_constraints = True
                self.dirty_position_constraints = True

            self.dirty_shape = False
            self.dirty_surface = True

        # ── 2. Position constraints (after size is stable) ────────────────────
        if self.dirty_position_constraints:
            self.resolve_constraints(position_only=True)
            self.dirty_position_constraints = False

        # ── 3. Layout (after our own rect is stable) ──────────────────────────
        if self.dirty_layout:
            self.layout.update_child_constraints()
            self.layout.arrange()
            self.dirty_layout = False
            self.dirty_surface = True

        # ── 4. Scroll (clamp first, then sync children) ───────────────────────
        old_scroll = self.scroll.xy
        self.clamp_scroll()

        if self.scroll.xy != old_scroll or self.dirty_scroll:
            self.layout.scroll_children()
            self.dirty_scroll = False
            self.dirty_surface = True

        # ── 5. Paint ──────────────────────────────────────────────────────────
        if self.dirty_surface and not skip_draw:
            self.paint()
            self.dirty_surface = False

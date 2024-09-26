import batFramework as bf
from .widget import Widget
from .constraints.constraints import *
from typing import Self, TYPE_CHECKING
from abc import ABC
import pygame

if TYPE_CHECKING:
    from .container import Container


class Layout(ABC):
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
        if self.parent:
            self.parent.dirty_children = True

    def arrange(self) -> None:
        return

    def get_raw_size(self) -> tuple[float, float]:
        """
        Returns the supposed size the container should have to encapsulate perfectly all of its widgets
        """
        return self.parent.rect.size if self.parent else (0, 0)

    def get_auto_size(self) -> tuple[float, float]:
        """
        Returns the final size the container should have (while keeping the the width and height if they are non-resizable)
        """
        target_size = list(self.get_raw_size())
        if not self.parent.autoresize_w:
            target_size[0] = self.parent.rect.w
        if not self.parent.autoresize_h:
            target_size[1] = self.parent.rect.h
        return target_size

    def focus_next_child(self) -> None:
        pass

    def focus_prev_child(self) -> None:
        pass

    def scroll_to_widget(self, widget: Widget) -> None:
        padded = self.parent.get_padded_rect()
        r = widget.rect
        if padded.contains(r):
            return
        clamped = r.clamp(padded)
        dx, dy = clamped.move(-r.x, -r.y).topleft
        self.parent.scroll_by((-dx, -dy))

    def handle_event(self, event):
        pass


class SingleAxisLayout(Layout):
    def focus_next_child(self) -> None:
        l = self.parent.get_interactive_children()
        self.parent.focused_index = min(self.parent.focused_index + 1, len(l) - 1)
        focused = l[self.parent.focused_index]
        focused.get_focus()
        self.scroll_to_widget(focused)

    def focus_prev_child(self) -> None:
        l = self.parent.get_interactive_children()
        self.parent.focused_index = max(self.parent.focused_index - 1, 0)
        focused = l[self.parent.focused_index]
        focused.get_focus()
        self.scroll_to_widget(focused)


class Column(SingleAxisLayout):
    def __init__(self, gap: int = 0, spacing: bf.spacing = bf.spacing.MANUAL):
        super().__init__()
        self.gap = gap
        self.spacing = spacing

    def set_gap(self, value: float) -> Self:
        self.gap = value
        self.notify_parent()
        return self

    def set_spacing(self, spacing: bf.spacing) -> Self:
        self.spacing = spacing
        self.notify_parent()
        return self

    def get_raw_size(self) -> tuple[float, float]:
        len_children = len(self.parent.children)
        if not len_children:
            return self.parent.rect.size
        parent_height = sum(c.get_min_required_size()[1] for c in self.parent.children)
        parent_width = max(c.get_min_required_size()[0] for c in self.parent.children)
        if self.gap:
            parent_height += (len_children - 1) * self.gap
        target_rect = self.parent.inflate_rect_by_padding(
            (0, 0, parent_width, parent_height)
        )
        return target_rect.size

    def get_auto_size(self) -> tuple[float, float]:
        target_size = list(self.get_raw_size())
        if not self.parent.autoresize_w:
            target_size[0] = self.parent.rect.w
        if not self.parent.autoresize_h:
            target_size[1] = self.parent.rect.h
        return target_size

    def arrange(self) -> None:
        if not self.parent or not self.parent.children:
            return
        if self.child_constraints:
            for child in self.parent.children:
                child.add_constraints(*self.child_constraints)
        self.child_rect = self.parent.get_padded_rect()

        if self.parent.autoresize_w or self.parent.autoresize_h:
            width, height = self.get_auto_size()
            if self.parent.rect.size != (width, height):
                self.parent.set_size((width, height))
                self.parent.build()
                self.arrange()
                return
        self.child_rect.move_ip(-self.parent.scroll.x, -self.parent.scroll.y)
        y = self.child_rect.top
        for child in self.parent.children:
            child.set_position(self.child_rect.x, y)
            y += child.get_min_required_size()[1] + self.gap

    def handle_event(self, event):
        if self.parent.autoresize_h or not self.parent.visible:
            return

        if not self.parent.children:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            r = self.parent.get_root()
            if not r:
                return

            if self.parent.rect.collidepoint(
                r.drawing_camera.screen_to_world(pygame.mouse.get_pos())
            ):
                if event.button == 4:
                    self.parent.scroll_by((0, -10))
                elif event.button == 5:
                    self.parent.scroll_by((0, 10))
                else:
                    return
                event.consumed = True
                self.parent.clamp_scroll()


class Row(SingleAxisLayout):
    def __init__(self, gap: int = 0, spacing: bf.spacing = bf.spacing.MANUAL):
        super().__init__()
        self.gap = gap
        self.spacing = spacing

    def set_gap(self, value: float) -> Self:
        self.gap = value
        self.notify_parent()
        return self

    def set_spacing(self, spacing: bf.spacing) -> Self:
        self.spacing = spacing
        self.notify_parent()
        return self

    def get_raw_size(self) -> tuple[float, float]:
        len_children = len(self.parent.children)
        if not len_children:
            return self.parent.rect.size
        parent_width = sum(c.get_min_required_size()[0] for c in self.parent.children)
        parent_height = max(c.get_min_required_size()[1] for c in self.parent.children)
        if self.gap:
            parent_width += (len_children - 1) * self.gap
        target_rect = self.parent.inflate_rect_by_padding(
            (0, 0, parent_width, parent_height)
        )

        return target_rect.size

    def get_auto_size(self) -> tuple[float, float]:
        target_size = list(self.get_raw_size())
        if not self.parent.autoresize_w:
            target_size[0] = self.parent.rect.w
        if not self.parent.autoresize_h:
            target_size[1] = self.parent.rect.h
        return target_size

    def arrange(self) -> None:
        if not self.parent or not self.parent.children:
            return
        if self.child_constraints:
            for child in self.parent.children:
                child.add_constraints(*self.child_constraints)
        self.child_rect = self.parent.get_padded_rect()

        if self.parent.autoresize_w or self.parent.autoresize_h:
            width, height = self.get_auto_size()
            if self.parent.rect.size != (width, height):
                self.parent.set_size((width, height))
                self.parent.build()
                self.arrange()
                return
        self.child_rect.move_ip(-self.parent.scroll.x, -self.parent.scroll.y)
        x = self.child_rect.left
        for child in self.parent.children:
            child.set_position(x, self.child_rect.y)
            x += child.get_min_required_size()[0] + self.gap

    def handle_event(self, event):
        if self.parent.autoresize_w or not self.parent.visible:
            return

        if not self.parent.children:
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            r = self.parent.get_root()
            if not r:
                return
            if self.parent.rect.collidepoint(
                r.drawing_camera.screen_to_world(pygame.mouse.get_pos())
            ):
                if event.button == 4:
                    self.parent.scroll_by((-10, 0))
                elif event.button == 5:
                    self.parent.scroll_by((10, 0))
                else:
                    return
                event.consumed = True
                self.parent.clamp_scroll()

import batFramework as bf
from .widget import Widget
from .constraints.constraints import *
from typing import Self, TYPE_CHECKING
from abc import ABC,abstractmethod
import pygame
from .interactiveWidget import InteractiveWidget

if TYPE_CHECKING:
    from .container import Container


class Layout(ABC):
    def __init__(self, parent: "Container" = None):
        self.parent = parent
        self.child_constraints: list[Constraint] = []
        self.children_rect = pygame.FRect(0, 0, 0, 0)

    def get_free_space(self)->tuple[float,float]:
        """
        return the space available for Growing widgets to use
        """
        return self.parent.get_inner_rect()

    def set_child_constraints(self, *constraints) -> Self:
        self.child_constraints = list(constraints)
        self.update_child_constraints()
        self.notify_parent()
        return self

    def set_parent(self, parent: Widget):
        self.parent = parent
        self.notify_parent()

    def notify_parent(self) -> None:
        if self.parent:
            self.parent.dirty_layout = True

    def update_children_rect(self):
        if self.parent.get_layout_children():
            self.children_rect = pygame.FRect(*self.parent.get_inner_rect().topleft,*self.parent.get_layout_children()[0].get_min_required_size())
            
            self.children_rect.unionall(
                [pygame.FRect(0,0,*c.get_min_required_size()) for c in self.parent.get_layout_children()[1:]]
            )
        else:
            self.children_rect = pygame.FRect(*self.parent.get_inner_rect().topleft, 0, 0)
        self.children_rect.move_ip(-self.parent.scroll.x,-self.parent.scroll.y)

    def update_child_constraints(self):
        if self.parent:
            for child in self.parent.get_layout_children():
                child.add_constraints(*self.child_constraints)

    def arrange(self) -> None:
        """
        updates the position of children in the parent
        """
        return

    def scroll_children(self)->None:
        return

    def get_raw_size(self):
        """
        Returns the size the container should have to encapsulate perfectly all of its widgets
        """
        # print(self,self.parent,len(self.parent.get_layout_children()))
        self.update_children_rect() # TODO: find  a way to call this fewer times
        return self.children_rect.size

    def get_auto_size(self) -> tuple[float, float]:
        """
        Returns the final size the container should have (while keeping the width and height if they are non-resizable)
        """
        target_size = list(self.get_raw_size())
        if not self.parent.autoresize_w:
            target_size[0] = self.parent.get_inner_width()
        if not self.parent.autoresize_h:
            target_size[1] = self.parent.get_inner_height()
        
        return self.parent.expand_rect_with_padding((0,0,*target_size)).size 
        # return target_size

    def scroll_to_widget(self, widget: "Widget"):
        """
        Scrolls parent container so that the widget becomes visible.
        If the widget is bigger than the container, aligns top/left.
        """
        inner = self.parent.get_inner_rect()

        if self.parent.clip_children and not inner.contains(widget.rect):
            scroll = pygame.Vector2(0, 0)

            # Horizontal
            if widget.rect.w > inner.w:
                # Widget is too wide: just align left
                if widget.rect.left < inner.left:
                    scroll.x = inner.left - widget.rect.left
            else:
                if widget.rect.left < inner.left:
                    scroll.x = inner.left - widget.rect.left
                elif widget.rect.right > inner.right:
                    scroll.x = inner.right - widget.rect.right

            # Vertical
            if widget.rect.h > inner.h:
                # Widget is too tall: just align top
                if widget.rect.top < inner.top:
                    scroll.y = inner.top - widget.rect.top
            else:
                if widget.rect.top < inner.top:
                    scroll.y = inner.top - widget.rect.top
                elif widget.rect.bottom > inner.bottom:
                    scroll.y = inner.bottom - widget.rect.bottom

            # Apply
            self.parent.scroll_by(-scroll)

        # stop at root
        if self.parent.is_root:
            return

        # recurse upwards if parent has a layout
        if hasattr(self.parent.parent, "layout"):
            self.parent.parent.layout.scroll_to_widget(widget)
    def handle_event(self, event):
        pass

class FreeLayout(Layout):...

class SingleAxisLayout(Layout):

    def __init__(self, parent = None):
        super().__init__(parent)

    def focus_next_child(self) -> None:
        l = self.parent.get_interactive_children()
        self.parent.focused_index = min(self.parent.focused_index + 1, len(l) - 1)
        focused = l[self.parent.focused_index]
        focused.get_focus()

    def focus_prev_child(self) -> None:
        l = self.parent.get_interactive_children()
        self.parent.focused_index = max(self.parent.focused_index - 1, 0)
        focused = l[self.parent.focused_index]
        focused.get_focus()

class DoubleAxisLayout(Layout):
    """Abstract layout class for layouts that arrange widgets in two dimensions."""

    def focus_up_child(self) -> None:...
    def focus_down_child(self) -> None:...
    def focus_right_child(self) -> None:...
    def focus_left_child(self) -> None:...

class Column(SingleAxisLayout):
    def __init__(self, gap: int = 0):
        super().__init__()
        self.gap = gap

    def handle_event(self, event):
        if not self.parent.get_layout_children() or not self.parent.children_has_focus():
            return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_UP):
                self.focus_next_child() if event.key == pygame.K_DOWN else self.focus_prev_child()
                event.consumed = True

    def update_children_rect(self):
        layout_children = self.parent.get_layout_children()
        if layout_children:
            width = max(child.get_min_required_size()[0] if child.autoresize_h else child.rect.w for child in layout_children )
            height = sum(child.get_min_required_size()[1]if child.autoresize_w else child.rect.h for child in layout_children) + self.gap * (len(layout_children) - 1)
            self.children_rect = pygame.FRect(*self.parent.get_inner_rect().topleft, width, height)
        else:
            self.children_rect = pygame.FRect(*self.parent.get_inner_rect().topleft, 10, 10)
        self.children_rect.move_ip(-self.parent.scroll.x,-self.parent.scroll.y)

    def scroll_children(self):
        topleft = list(self.parent.get_inner_rect().topleft)
        topleft[0] -= round(self.parent.scroll.x)
        topleft[1] -= round(self.parent.scroll.y)
        layout_children = self.parent.get_layout_children()
        for child in layout_children:
            child.set_position(*topleft)
            topleft[1] += child.rect.height + self.gap

    def arrange(self) -> None:
        self.update_children_rect()
        self.scroll_children()

class Row(SingleAxisLayout):
    def __init__(self, gap: int = 0):
        super().__init__()
        self.gap = gap

    def handle_event(self, event):
        if not self.parent.get_layout_children() or not self.parent.children_has_focus():
            return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RIGHT, pygame.K_LEFT):
                self.focus_next_child() if event.key == pygame.K_RIGHT else self.focus_prev_child()
                event.consumed = True

    def update_children_rect(self):
        layout_children = self.parent.get_layout_children()
        if layout_children:
            width = sum(child.get_min_required_size()[0] if child.autoresize_w else child.rect.w for child in layout_children ) + self.gap * (len(layout_children) - 1)
            height = max(child.get_min_required_size()[1] if child.autoresize_h else child.rect.h for child in layout_children )
            self.children_rect = pygame.FRect(*self.parent.get_inner_rect().topleft, width, height)
        else:
            self.children_rect = pygame.FRect(*self.parent.get_inner_rect().topleft, 10,10)        
        self.children_rect.move_ip(-self.parent.scroll.x,-self.parent.scroll.y)

    def scroll_children(self):
        topleft = list(self.parent.get_inner_rect().topleft)
        topleft[0] -= round(self.parent.scroll.x)
        topleft[1] -= round(self.parent.scroll.y)
        layout_children = self.parent.get_layout_children()
        for child in layout_children:
            child.set_position(*topleft)
            topleft[0] += child.rect.width + self.gap

    def arrange(self) -> None:
        self.update_children_rect()
        self.scroll_children()

class Grid(DoubleAxisLayout):
    def __init__(self, rows: int, cols: int, gap: int = 0):
        super().__init__()
        self.rows = rows
        self.cols = cols
        self.gap = gap

    def focus_up_child(self) -> None:
        l = self.parent.get_interactive_children()
        if not l:
            return
        current_index = self.parent.focused_index
        if current_index == -1:
            return
        current_row = current_index // self.cols
        target_index = max(0, current_index - self.cols)
        if target_index // self.cols < current_row:
            self.parent.focused_index = target_index
            l[target_index].get_focus()

    def focus_down_child(self) -> None:
        l = self.parent.get_interactive_children()
        if not l:
            return
        current_index = self.parent.focused_index
        if current_index == -1:
            return
        current_row = current_index // self.cols
        target_index = min(len(l) - 1, current_index + self.cols)
        if target_index // self.cols > current_row:
            self.parent.focused_index = target_index
            l[target_index].get_focus()

    def focus_left_child(self) -> None:
        l = self.parent.get_interactive_children()
        if not l:
            return
        current_index = self.parent.focused_index
        if current_index == -1:
            return
        target_index = max(0, current_index - 1)
        if target_index // self.cols == current_index // self.cols:
            self.parent.focused_index = target_index
            l[target_index].get_focus()

    def focus_right_child(self) -> None:
        l = self.parent.get_interactive_children()
        if not l:
            return
        current_index = self.parent.focused_index
        if current_index == -1:
            return
        target_index = min(len(l) - 1, current_index + 1)
        if target_index // self.cols == current_index // self.cols:
            self.parent.focused_index = target_index
            l[target_index].get_focus()

    def handle_event(self, event):
        if not self.parent.get_layout_children() or not self.parent.children_has_focus():
            return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RIGHT, pygame.K_LEFT, pygame.K_UP, pygame.K_DOWN):
                if event.key == pygame.K_RIGHT:
                    self.focus_right_child()
                elif event.key == pygame.K_LEFT:
                    self.focus_left_child()
                elif event.key == pygame.K_UP:
                    self.focus_up_child()
                elif event.key == pygame.K_DOWN:
                    self.focus_down_child()
                
                event.consumed = True

    def update_children_rect(self):
        layout_children = self.parent.get_layout_children() 
        if layout_children:
            cell_width = max(child.get_min_required_size()[0] for child in layout_children)
            cell_height = max(child.get_min_required_size()[1] for child in layout_children)
            width = self.cols * cell_width + self.gap * (self.cols - 1)
            height = self.rows * cell_height + self.gap * (self.rows - 1)
            self.children_rect = pygame.FRect(*self.parent.get_inner_rect().topleft, width, height)
        else:
            self.children_rect = pygame.FRect(*self.parent.get_inner_rect().topleft, 10, 10)
        self.children_rect.move_ip(-self.parent.scroll.x, -self.parent.scroll.y)

    def scroll_children(self):
        topleft = list(self.parent.get_inner_rect().topleft)
        topleft[0] -= round(self.parent.scroll.x)
        topleft[1] -= round(self.parent.scroll.y)
        layout_children = self.parent.get_layout_children()
        cell_width = (self.children_rect.width - self.gap * (self.cols - 1)) / self.cols if self.cols else 0
        cell_height = (self.children_rect.height - self.gap * (self.rows - 1)) / self.rows if self.rows else 0
        for i, child in enumerate(layout_children):
            row = i // self.cols
            col = i % self.cols
            x = topleft[0] + col * (cell_width + self.gap)
            y = topleft[1] + row * (cell_height + self.gap)
            child.set_position(x, y)

    def arrange(self) -> None:
        self.update_children_rect()
        self.scroll_children()

class RowFill(Row):

    def update_children_rect(self):
        parent_width = self.parent.get_inner_width()
        if self.parent.get_layout_children():
            height = max(child.get_min_required_size()[1] for child in self.parent.get_layout_children())
            width = parent_width
            self.children_rect = pygame.FRect(*self.parent.get_inner_rect().topleft, width, height)
        else:
            self.children_rect = pygame.FRect(*self.parent.get_inner_rect().topleft, parent_width,10)        
        self.children_rect.move_ip(-self.parent.scroll.x,-self.parent.scroll.y)

    def scroll_children(self):
        topleft = list(self.parent.get_inner_rect().topleft)
        topleft[0] -= round(self.parent.scroll.x)
        topleft[1] -= round(self.parent.scroll.y)
        layout_children = self.parent.get_layout_children()
        total_gap = self.gap * (len(layout_children) - 1)
        available_width = max(0, self.children_rect.width - total_gap)
        child_width = available_width / len(layout_children) if layout_children else 0
        for child in layout_children:
            child.set_position(*topleft)
            topleft[0] += child_width + self.gap

    def resize_children(self):
        layout_children = self.parent.get_layout_children()
        total_gap = self.gap * (len(layout_children) - 1)
        available_width = max(0, self.children_rect.width - total_gap)
        child_width = available_width / len(layout_children) if layout_children else 0
        for child in layout_children:
            child.set_autoresize_w(False)
            child.set_size((child_width, None))

    def arrange(self) -> None:
        self.update_children_rect()
        self.resize_children()
        self.scroll_children()

class ColumnFill(Column):

    def update_children_rect(self):
        parent_height = self.parent.get_inner_height()
        if self.parent.get_layout_children():
            width = max(child.get_min_required_size()[0] for child in self.parent.get_layout_children())
            height = parent_height
            self.children_rect = pygame.FRect(*self.parent.get_inner_rect().topleft, width, height)
        else:
            self.children_rect = pygame.FRect(*self.parent.get_inner_rect().topleft, 10, parent_height)
        self.children_rect.move_ip(-self.parent.scroll.x, -self.parent.scroll.y)

    def scroll_children(self):
        topleft = list(self.parent.get_inner_rect().topleft)
        topleft[0] -= round(self.parent.scroll.x)
        topleft[1] -= round(self.parent.scroll.y)
        layout_children = self.parent.get_layout_children()
        total_gap = self.gap * (len(layout_children) - 1)
        available_height = max(0, self.children_rect.height - total_gap)
        child_height = available_height / len(layout_children) if layout_children else 0
        for child in layout_children:
            child.set_position(*topleft)
            topleft[1] += child_height + self.gap

    def resize_children(self):
        layout_children = self.parent.get_layout_children()
        total_gap = self.gap * (len(layout_children) - 1)
        available_height = max(0, self.children_rect.height - total_gap)
        child_height = available_height / len(layout_children) if layout_children else 0
        for child in layout_children:
            child.set_autoresize_h(False)
            child.set_size((None, child_height))

    def arrange(self) -> None:
        self.update_children_rect()
        self.resize_children()
        self.scroll_children()

class GridFill(Grid):
    def update_children_rect(self):
        self.children_rect = self.parent.get_inner_rect()

    def scroll_children(self):
        topleft = list(self.parent.get_inner_rect().topleft)
        topleft[0] -= round(self.parent.scroll.x)
        topleft[1] -= round(self.parent.scroll.y)
        layout_children = self.parent.get_layout_children()
        cell_width = (self.children_rect.width - self.gap * (self.cols - 1)) / self.cols if self.cols else 0
        cell_height = (self.children_rect.height - self.gap * (self.rows - 1)) / self.rows if self.rows else 0
        for i, child in enumerate(layout_children):
            row = i // self.cols
            col = i % self.cols
            x = round(topleft[0] + col * (cell_width + self.gap))
            y = round(topleft[1] + row * (cell_height + self.gap))
            child.set_position(x, y)

    def resize_children(self):
        layout_children = self.parent.get_layout_children()
        cell_width = (self.children_rect.width - self.gap * (self.cols - 1)) / self.cols if self.cols else 0
        cell_height = (self.children_rect.height - self.gap * (self.rows - 1)) / self.rows if self.rows else 0
        for child in layout_children:
            child.set_autoresize(False)
            child.set_size((cell_width, cell_height))

    def arrange(self) -> None:
        print("arrange grid fill")
        self.update_children_rect()
        self.resize_children()
        self.scroll_children()

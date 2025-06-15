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

    def get_raw_size(self):
        """
        Returns the size the container should have to encapsulate perfectly all of its widgets
        """
        # print(self,self.parent,len(self.parent.get_layout_children()))
        self.update_children_rect()
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
        Scrolls parent containers so that the widget becomes visible.
        Handles deeply nested widgets and large widgets gracefully.
        """
        target = widget
        container = self.parent

        while container and not container.is_root:
            if not hasattr(container,"scroll"):
                container = container.parent
                continue
            target_rect = target.rect  # global
            padded_rect = container.get_inner_rect()  # global

            dx = dy = 0

            # --- Horizontal ---
            if target_rect.width <= padded_rect.width:
                if target_rect.left < padded_rect.left:
                    dx = target_rect.left - padded_rect.left
                elif target_rect.right > padded_rect.right:
                    dx = target_rect.right - padded_rect.right
            else:
                # Widget is wider than viewport: align left side
                if target_rect.left < padded_rect.left:
                    dx = target_rect.left - padded_rect.left
                elif target_rect.right > padded_rect.right:
                    dx = target_rect.right - padded_rect.right

            # --- Vertical ---
            if target_rect.height <= padded_rect.height:
                if target_rect.top < padded_rect.top:
                    dy = target_rect.top - padded_rect.top
                elif target_rect.bottom > padded_rect.bottom:
                    dy = target_rect.bottom - padded_rect.bottom
            else:
                # Widget is taller than viewport: align top side
                if target_rect.top < padded_rect.top:
                    dy = target_rect.top - padded_rect.top
                elif target_rect.bottom > padded_rect.bottom:
                    dy = target_rect.bottom - padded_rect.bottom

            # Convert global delta into local scroll delta for container
            container.scroll_by((dx, dy))

            # Now the target for the next iteration is the container itself
            target = container
            container = container.parent


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

    def update_children_rect(self):
        if self.parent.get_layout_children():
            width = max(child.get_min_required_size()[0] for child in self.parent.get_layout_children() )
            height = sum(child.get_min_required_size()[1] for child in self.parent.get_layout_children()) + self.gap * (len(self.parent.get_layout_children()) - 1)

            # width = max(child.rect.w for child in self.parent.get_layout_children() )
            # height = sum(child.rect.h for child in self.parent.get_layout_children()) + self.gap * (len(self.parent.get_layout_children()) - 1)


            self.children_rect = pygame.FRect(*self.parent.get_inner_rect().topleft, width, height)
        else:
            self.children_rect = pygame.FRect(*self.parent.get_inner_rect().topleft, 10, 10)
        self.children_rect.move_ip(-self.parent.scroll.x,-self.parent.scroll.y)

    def handle_event(self, event):
        if not self.parent.get_layout_children() or not self.parent.children_has_focus():
            return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_UP):
                self.focus_next_child() if event.key == pygame.K_DOWN else self.focus_prev_child()
                event.consumed = True
                event.consumed = True


    def arrange(self) -> None:
        self.update_children_rect()
        y = self.children_rect.y
        for child in self.parent.get_layout_children():
            child.set_position(self.children_rect.x, y)
            y += child.rect.height + self.gap

class Row(SingleAxisLayout):
    def __init__(self, gap: int = 0):
        super().__init__()
        self.gap = gap

    def update_children_rect(self):
        if self.parent.get_layout_children():
            height = max(child.get_min_required_size()[1] for child in self.parent.get_layout_children())
            width = sum(child.get_min_required_size()[0] for child in self.parent.get_layout_children()) + self.gap * (len(self.parent.get_layout_children()) - 1)
            self.children_rect = pygame.FRect(*self.parent.get_inner_rect().topleft, width, height)
        else:
            self.children_rect = pygame.FRect(*self.parent.get_inner_rect().topleft, 10,10)        
        self.children_rect.move_ip(-self.parent.scroll.x,-self.parent.scroll.y)

    def handle_event(self, event):
        if not self.parent.get_layout_children() or not self.parent.children_has_focus():
            return

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RIGHT, pygame.K_LEFT):
                self.focus_next_child() if event.key == pygame.K_RIGHT else self.focus_prev_child()
                event.consumed = True


    def arrange(self) -> None:
        self.update_children_rect()
        x = self.children_rect.x
        for child in self.parent.get_layout_children():
            child.set_position(x,self.children_rect.y)
            x += child.rect.width + self.gap



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


    def arrange(self) -> None:
        """
        Arranges children in a row and resizes them to fill the parent's height,
        accounting for the gap between children.
        """
        self.update_children_rect()
        for child in self.parent.get_layout_children():
            child.set_autoresize_w(False)
        x = self.children_rect.x
        # available_height = self.children_rect.height

        # Calculate the width available for each child
        total_gap = self.gap * (len(self.parent.get_layout_children()) - 1)
        available_width = max(0, self.children_rect.width - total_gap)
        child_width = available_width / len(self.parent.get_layout_children()) if self.parent.get_layout_children() else 0

        for child in self.parent.get_layout_children():
            child.set_size((child_width, None))  # Resize child to fill height
            child.set_position(x, self.children_rect.y)  # Position child
            x += child_width + self.gap


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

    def arrange(self) -> None:
        """
        Arranges children in a column and resizes them to fill the parent's width,
        accounting for the gap between children.
        """
        self.update_children_rect()
        for child in self.parent.get_layout_children():
            child.set_autoresize_h(False)
        y = self.children_rect.y

        # Calculate the height available for each child
        total_gap = self.gap * (len(self.parent.get_layout_children()) - 1)
        available_height = max(0, self.children_rect.height - total_gap)
        child_height = available_height / len(self.parent.get_layout_children()) if self.parent.get_layout_children() else 0

        for child in self.parent.get_layout_children():
            child.set_size((None, child_height))  # Resize child to fill width
            child.set_position(self.children_rect.x, y)  # Position child
            y += child_height + self.gap


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
        if self.parent.get_layout_children():
            cell_width = max(child.get_min_required_size()[0] for child in self.parent.get_layout_children())
            cell_height = max(child.get_min_required_size()[1] for child in self.parent.get_layout_children())
            width = self.cols * cell_width + self.gap * (self.cols - 1)
            height = self.rows * cell_height + self.gap * (self.rows - 1)
            self.children_rect = pygame.FRect(*self.parent.get_inner_rect().topleft, width, height)
        else:
            self.children_rect = pygame.FRect(*self.parent.get_inner_rect().topleft, 10, 10)
        self.children_rect.move_ip(-self.parent.scroll.x, -self.parent.scroll.y)

    def arrange(self) -> None:
        self.update_children_rect()
        if not self.parent.get_layout_children():
            return

        cell_width = (self.children_rect.width - self.gap * (self.cols - 1)) / self.cols
        cell_height = (self.children_rect.height - self.gap * (self.rows - 1)) / self.rows

        for i, child in enumerate(self.parent.get_layout_children()):
            row = i // self.cols
            col = i % self.cols
            x = self.children_rect.x + col * (cell_width + self.gap)
            y = self.children_rect.y + row * (cell_height + self.gap)
            child.set_size((cell_width, cell_height))
            child.set_position(x, y)


class GridFill(Grid):
    def update_children_rect(self):
        self.children_rect = self.parent.get_inner_rect()
    def arrange(self) -> None:
        """
        Arranges children in a grid and resizes them to fill the parent's available space,
        accounting for the gap between children.
        """
        self.update_children_rect()
            
        if not self.parent.get_layout_children():
            return
        for child in self.parent.get_layout_children():
            child.set_autoresize(False)

        cell_width = (self.children_rect.width - self.gap * (self.cols - 1)) / self.cols
        cell_height = (self.children_rect.height - self.gap * (self.rows - 1)) / self.rows

        for i, child in enumerate(self.parent.get_layout_children()):
            row = i // self.cols
            col = i % self.cols
            x = self.children_rect.x + col * (cell_width + self.gap)
            y = self.children_rect.y + row * (cell_height + self.gap)
            child.set_size((cell_width, cell_height))
            child.set_position(x, y)
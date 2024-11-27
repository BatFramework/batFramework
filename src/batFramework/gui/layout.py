import batFramework as bf
from .widget import Widget
from .constraints.constraints import *
from typing import Self, TYPE_CHECKING
from abc import ABC,abstractmethod
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
            self.parent.dirty_layout = True

    def arrange(self) -> None:
        return

    def get_raw_size(self) -> tuple[float, float]:
        """
        Returns the supposed size the container should have to encapsulate perfectly all of its widgets
        """
        return self.parent.rect.size if self.parent else (0, 0)

    def get_auto_size(self) -> tuple[float, float]:
        """
        Returns the final size the container should have (while keeping the width and height if they are non-resizable)
        """
        target_size = list(self.get_raw_size())
        if not self.parent.autoresize_w:
            target_size[0] = self.parent.rect.w
        if not self.parent.autoresize_h:
            target_size[1] = self.parent.rect.h
        return target_size

    def scroll_to_widget(self, widget: Widget) -> None:
        padded = self.parent.get_padded_rect() # le carré intérieur
        r = widget.rect # le carré du widget = Button
        if padded.contains(r): # le widget ne depasse pas -> OK
            return
        clamped = r.clamp(padded)
        # clamped.move_ip(-self.parent.rect.x,-self.parent.rect.y)
        dx,dy = clamped.x - r.x,clamped.y-r.y

        self.parent.scroll_by((-dx, -dy)) # on scroll la différence pour afficher le bouton en entier
        
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
        self.children_rect = self.parent.get_padded_rect()

        width, height = self.get_auto_size()
        if self.parent.autoresize_w and self.parent.rect.w !=width:
            self.parent.set_size((width,None))
        if self.parent.autoresize_h and self.parent.rect.h !=height:
            self.parent.set_size((None,height))
        
        # if self.parent.dirty_shape:
            # print("parent set dirty shape")
            # self.parent.dirty_layout = True
            # self.parent.apply_updates()
            # self.arrange()
            # return
            
        self.children_rect.move_ip(-self.parent.scroll.x, -self.parent.scroll.y)
        y = self.children_rect.top
        for child in self.parent.children:
            child.set_position(self.children_rect.x, y)
            y += child.get_min_required_size()[1] + self.gap

    def handle_event(self, event):
        if not self.parent.children:
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self.focus_next_child()
            elif event.key == pygame.K_UP:
                self.focus_prev_child()
            else:
                return
        elif event.type == pygame.MOUSEBUTTONDOWN:
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
                self.parent.clamp_scroll()
            else:
                return
        else:
            return
        event.consumed = True

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
        self.children_rect = self.parent.get_padded_rect()

        if self.parent.autoresize_w or self.parent.autoresize_h:
            width, height = self.get_auto_size()
            if self.parent.rect.size != (width, height):
                self.parent.set_size((width, height))
                self.parent.build()
                self.arrange()
                return
        self.children_rect.move_ip(-self.parent.scroll.x, -self.parent.scroll.y)
        x = self.children_rect.left
        for child in self.parent.children:
            child.set_position(x, self.children_rect.y)
            x += child.get_min_required_size()[0] + self.gap

    def handle_event(self, event):
        if not self.parent.children:
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                self.focus_next_child()
            elif event.key == pygame.K_LEFT:
                self.focus_prev_child()
            else:
                return
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
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
                self.parent.clamp_scroll()
            else:
                return
        else:
            return


        event.consumed = True

class RowFill(Row):
    def __init__(self, gap: int = 0, spacing: bf.spacing = bf.spacing.MANUAL):
        super().__init__(gap, spacing)

    def arrange(self) -> None:
        if self.parent.autoresize_w :
           super().arrange() 
           return
        if not self.parent or not self.parent.children:
            return

        if self.child_constraints:
            for child in self.parent.children:
                child.add_constraints(*self.child_constraints)
        self.children_rect = self.parent.get_padded_rect()

        if self.parent.autoresize_w or self.parent.autoresize_h:
            width, height = self.get_auto_size()
            if self.parent.rect.size != (width, height):
                self.parent.set_size((width, height))
                self.parent.build()
                self.arrange()
                return

        self.children_rect.move_ip(-self.parent.scroll.x, -self.parent.scroll.y)
        
        # Calculate the width each child should fill
        available_width = self.children_rect.width - (len(self.parent.children) - 1) * self.gap
        child_width = available_width / len(self.parent.children)
        
        x = self.children_rect.left
        for child in self.parent.children:
            child.set_position(x, self.children_rect.y)
            child.set_autoresize_w(False)
            child.set_size((child_width, None))
            x += child_width + self.gap

    def get_raw_size(self) -> tuple[float, float]:
        """Calculate total size with children widths filling the available space."""
        if self.parent.autoresize_h :
           return super().get_raw_size()
        len_children = len(self.parent.children)
        if not len_children:
            return self.parent.rect.size
        parent_height = max(c.get_min_required_size()[1] for c in self.parent.children)
        target_rect = self.parent.inflate_rect_by_padding((0, 0, self.children_rect.width, parent_height))
        return target_rect.size


class ColumnFill(Column):
    def __init__(self, gap: int = 0, spacing: bf.spacing = bf.spacing.MANUAL):
        super().__init__(gap, spacing)

    def arrange(self) -> None:
        if self.parent.autoresize_h :
           super().arrange() 
           return
        if not self.parent or not self.parent.children:
            return
        if self.child_constraints:
            for child in self.parent.children:
                child.add_constraints(*self.child_constraints)
        self.children_rect = self.parent.get_padded_rect()

        if self.parent.autoresize_w or self.parent.autoresize_h:
            width, height = self.get_auto_size()
            if self.parent.rect.size != (width, height):
                self.parent.set_size((width, height))
                self.parent.build()
                self.arrange()
                return

        self.children_rect.move_ip(-self.parent.scroll.x, -self.parent.scroll.y)

        # Calculate the height each child should fill
        available_height = self.children_rect.height - (len(self.parent.children) - 1) * self.gap
        child_height = available_height / len(self.parent.children)

        y = self.children_rect.top
        for child in self.parent.children:
            child.set_position(self.children_rect.x, y)
            child.set_autoresize_h(False)
            child.set_size((None, child_height))
            y += child_height + self.gap

    def get_raw_size(self) -> tuple[float, float]:
        """Calculate total size with children heights filling the available space."""
        if self.parent.autoresize_w :
           return super().get_raw_size()
        len_children = len(self.parent.children)
        if not len_children:
            return self.parent.rect.size
        parent_width = max(c.get_min_required_size()[0] for c in self.parent.children)
        target_rect = self.parent.inflate_rect_by_padding((0, 0, parent_width, self.children_rect.height))
        return target_rect.size



class DoubleAxisLayout(Layout):
    """Abstract layout class for layouts that arrange widgets in two dimensions."""

    @abstractmethod
    def arrange(self) -> None:
        """Arrange child widgets across both axes, implementation required in subclasses."""
        pass

    def focus_up_child(self) -> None:...
    def focus_down_child(self) -> None:...
    def focus_right_child(self) -> None:...
    def focus_left_child(self) -> None:...



class Grid(DoubleAxisLayout):
    def __init__(self, rows: int, cols: int, gap: int = 0):
        super().__init__()
        self.rows = rows
        self.cols = cols
        self.gap = gap

    def set_gap(self, value: int) -> Self:
        self.gap = value
        self.notify_parent()
        return self

    def set_dimensions(self, rows: int, cols: int) -> Self:
        self.rows = rows
        self.cols = cols
        self.notify_parent()
        return self

    def get_raw_size(self) -> tuple[float, float]:
        """Calculate raw size based on the max width and height needed to fit all children."""
        if not self.parent.children:
            return self.parent.rect.size

        # Calculate necessary width and height for the grid
        max_child_width = max(child.get_min_required_size()[0] for child in self.parent.children)
        max_child_height = max(child.get_min_required_size()[1] for child in self.parent.children)
        
        grid_width = self.cols * max_child_width + (self.cols - 1) * self.gap
        grid_height = self.rows * max_child_height + (self.rows - 1) * self.gap
        target_rect = self.parent.inflate_rect_by_padding((0, 0, grid_width, grid_height))
        
        return target_rect.size

    def arrange(self) -> None:
        """Arrange widgets in a grid with specified rows and columns."""
        if not self.parent or not self.parent.children:
            return

        if self.child_constraints:
            for child in self.parent.children:
                child.add_constraints(*self.child_constraints)


        if self.parent.autoresize_w or self.parent.autoresize_h:
            width, height = self.get_auto_size()
            if self.parent.rect.size != (width, height):
                self.parent.set_size((width, height))
                self.parent.build()
                self.arrange()
                return

        self.child_rect = self.parent.get_padded_rect()

        # Calculate cell width and height based on parent size and gaps
        cell_width = (self.child_rect.width - (self.cols - 1) * self.gap) / self.cols
        cell_height = (self.child_rect.height - (self.rows - 1) * self.gap) / self.rows

        for i, child in enumerate(self.parent.children):
            row = i // self.cols
            col = i % self.cols
            x = self.child_rect.left + col * (cell_width + self.gap)
            y = self.child_rect.top + row * (cell_height + self.gap)

            child.set_position(x, y)
            child.set_size((cell_width, cell_height))

    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self.focus_down_child()
            elif event.key == pygame.K_UP:
                self.focus_up_child()
            elif event.key == pygame.K_LEFT:
                self.focus_left_child()
            elif event.key == pygame.K_RIGHT:
                self.focus_right_child()         
            else:
                return
        elif event.type == pygame.MOUSEBUTTONDOWN:
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
                self.parent.clamp_scroll()
            else:
                return
        else:
            return
        event.consumed = True

    def focus_down_child(self) -> None:
        l = self.parent.get_interactive_children()
        new_index = self.parent.focused_index + self.cols
        if new_index >= len(l):
            return
        self.parent.focused_index = new_index
        focused = l[self.parent.focused_index]
        focused.get_focus()
        self.scroll_to_widget(focused)

    def focus_up_child(self) -> None:
        l = self.parent.get_interactive_children()
        new_index = self.parent.focused_index - self.cols
        if new_index < 0:
            return
        self.parent.focused_index = new_index
        focused = l[self.parent.focused_index]
        focused.get_focus()
        self.scroll_to_widget(focused)

    def focus_left_child(self) -> None:
        l = self.parent.get_interactive_children()
        new_index = (self.parent.focused_index % self.cols) -1
        if new_index < 0:
            return
        self.parent.focused_index -=1
        focused = l[self.parent.focused_index]
        focused.get_focus()
        self.scroll_to_widget(focused)

    def focus_right_child(self) -> None:
        l = self.parent.get_interactive_children()
        new_index = (self.parent.focused_index % self.cols) +1
        if new_index >= self.cols or self.parent.focused_index+1 >= len(l):
            return
        self.parent.focused_index += 1
        focused = l[self.parent.focused_index]
        focused.get_focus()
        self.scroll_to_widget(focused)


class GridFill(Grid):
    def __init__(self, rows: int, cols: int, gap: int = 0):
        super().__init__(rows,cols,gap)

    def arrange(self) -> None:
        """Arrange widgets to fill each grid cell, adjusting to available space."""
        if not self.parent or not self.parent.children:
            return

        if self.child_constraints:
            for child in self.parent.children:
                child.add_constraints(*self.child_constraints)

        self.child_rect = self.parent.get_padded_rect()

        # If autoresize is enabled, calculate required dimensions
        if self.parent.autoresize_w or self.parent.autoresize_h:
            width, height = self.get_auto_size()
            if self.parent.rect.size != (width, height):
                self.parent.set_size((width, height))
                self.parent.build()
                self.arrange()
                return

        # Adjust for scrolling offset
        self.child_rect.move_ip(-self.parent.scroll.x, -self.parent.scroll.y)

        # Calculate cell dimensions based on available space
        available_width = self.child_rect.width - (self.cols - 1) * self.gap
        available_height = self.child_rect.height - (self.rows - 1) * self.gap
        cell_width = available_width / self.cols
        cell_height = available_height / self.rows

        # Position each child in the grid
        for index, child in enumerate(self.parent.children):
            row = index // self.cols
            col = index % self.cols
            x = self.child_rect.left + col * (cell_width + self.gap)
            y = self.child_rect.top + row * (cell_height + self.gap)

            child.set_position(x, y)
            child.set_autoresize_w(False)
            child.set_autoresize_h(False)
            child.set_size((cell_width, cell_height))

    def get_raw_size(self) -> tuple[float, float]:
        """Calculate the grid’s raw size based on child minimums and the grid dimensions."""
        if not self.parent.children:
            return self.parent.rect.size

        # Determine minimum cell size required by the largest child
        max_child_width = max(child.get_min_required_size()[0] for child in self.parent.children)
        max_child_height = max(child.get_min_required_size()[1] for child in self.parent.children)

        # Calculate total required size for the grid
        grid_width = self.cols * max_child_width + (self.cols - 1) * self.gap
        grid_height = self.rows * max_child_height + (self.rows - 1) * self.gap

        # Adjust for padding and return
        target_rect = self.parent.inflate_rect_by_padding((0, 0, grid_width, grid_height))
        return target_rect.size

from __future__ import annotations
from math import isfinite
import logging
from typing import Self
import pygame
import batFramework as bf
from .widget import Widget
from .constraints.constraints import *


logger = logging.getLogger(__name__)

class Layout:
    """Measure child preferences, then assign child rectangles top down."""

    axis = None
    fill = False

    def __init__(self, parent=None):
        self.parent = parent
        self.child_constraints = []
        self.children_rect = pygame.FRect(0, 0, 0, 0)
        self.gap = 0
        self.alignment = None
        self.desired_size = (0, 0)
        self._effective_gap = 0

    def set_parent(self, parent):
        self.parent = parent
        self.mark_dirty()

    def mark_dirty(self):
        if self.parent:
            self.parent.dirty_surface = True

    def set_child_constraints(self, *constraints) -> Self:
        if self.parent:
            for child in self.parent.get_layout_children():
                child.remove_constraints(*(c.name for c in self.child_constraints))
        self.child_constraints = list(constraints)
        self.update_children_state()
        self.mark_dirty()
        return self

    def update_children_state(self):
        if self.parent:
            for child in self.parent.get_layout_children():
                child.add_constraints(*self.child_constraints)

    def _weight(self, child):
        if self.fill:
            return 1
        for constraint in child.constraints:
            if isinstance(constraint, Grow) and constraint.axis == self.axis:
                return constraint.weight
        return 0

    def _sizes(self, available, measure=False):
        children = self.parent.get_layout_children()
        sizes = {}
        if self.axis is None:
            for child in children:
                sizes[child] = (child.measure(available) if measure else
                                child.constrain_size(child.desired_size, available))
            return sizes
        axis = self.axis
        self._effective_gap = min(self.gap, available[axis] / max(1, len(children) - 1))
        remaining = max(0, available[axis] - max(0, len(children) - 1) * self._effective_gap)
        weights = {c: self._weight(c) for c in children}
        # Fixed children choose first. Growers share what remains, once.
        for child in children:
            if weights[child] > 0:
                continue
            offer = list(available)
            offer[axis] = remaining
            size = child.measure(offer) if measure else child.constrain_size(child.desired_size, offer)
            sizes[child] = size
            remaining = max(0, remaining - size[axis])
        total_weight = sum(weights.values())
        for child in children:
            if weights[child] <= 0:
                continue
            offer = list(available)
            offer[axis] = remaining * weights[child] / total_weight
            size = list(child.measure(offer) if measure else child.constrain_size(child.desired_size, offer))
            if not measure and isfinite(offer[axis]):
                size[axis] = offer[axis]
                size = child.constrain_size(size, offer)
            sizes[child] = tuple(size)
        return sizes

    def _extent(self, sizes):
        if not sizes:
            return (0, 0)
        if self.axis is None:
            # Free positions are relative to the parent's content origin.
            origin = self.parent.get_inner_rect().topleft
            return tuple(max((0 if any(con.affects_position for con in c.constraints)
                              else max(0, c.rect[i] - origin[i])) + s[i]
                             for c, s in sizes.items()) for i in (0, 1))
        axis = self.axis
        result = [0, 0]
        result[axis] = sum(s[axis] for s in sizes.values()) + self._effective_gap * max(0, len(sizes) - 1)
        result[1-axis] = max(s[1-axis] for s in sizes.values())
        return tuple(result)

    def measure(self, available_size):
        self.update_children_state()
        sizes = self._sizes(available_size, measure=True)
        self.desired_size = self._extent(sizes)
        return self.desired_size

    def _rects(self, inner, sizes):
        if self.axis is None:
            return {c: pygame.FRect(*c.rect.topleft, *s) for c, s in sizes.items()}
        result = {}
        cursor = inner[self.axis] - self.parent.scroll[self.axis]
        cross = 1 - self.axis
        for child in self.parent.get_layout_children():
            size = sizes[child]
            rect = pygame.FRect(*inner.topleft, *size)
            if self.alignment is not None:
                anchor = self.alignment.value
                setattr(rect, anchor, getattr(inner, anchor))
            rect[self.axis] = cursor
            rect[cross] -= self.parent.scroll[cross]
            result[child] = rect
            cursor += size[self.axis] + self._effective_gap
        return result

    def arrange(self):
        inner = self.parent.get_inner_rect()
        available = self.parent.get_layout_available_size(inner.size)
        sizes = self._sizes(available)
        extent = self._extent(sizes)
        self.children_rect = pygame.FRect(*inner.topleft, *extent)
        self.parent.clamp_scroll()
        arranged_scroll = self.parent.scroll.copy()
        for child, rect in self._rects(inner, sizes).items():
            child.arrange(rect)
        # An edited input can scroll its focus area during arrangement. Apply
        # that translation to every sibling before painting, without relayout.
        delta = arranged_scroll - self.parent.scroll
        if delta:
            for child in self.parent.get_layout_children():
                child.set_position(child.rect.x + delta.x, child.rect.y + delta.y)

    def get_raw_size(self):
        return self._extent({c: c.desired_size for c in self.parent.get_layout_children()})

    def scroll_to_widget(self, widget: "Widget",focus_area:pygame.Rect=None):
        """
        Scrolls parent container so that the widget becomes visible.
        If the widget is bigger than the container, aligns top/left.
        """
        inner = self.parent.get_inner_rect()
        if focus_area is None : focus_area = widget.rect
        if self.parent.clip_children and not inner.contains(focus_area):
            scroll = pygame.Vector2(0, 0)

            # Horizontal
            if focus_area.w > inner.w:
                # Widget is too wide: just align left
                if focus_area.left < inner.left:
                    scroll.x = inner.left - focus_area.left
            else:
                if focus_area.left < inner.left:
                    scroll.x = inner.left - focus_area.left
                elif focus_area.right > inner.right:
                    scroll.x = inner.right - focus_area.right

            # Vertical
            if focus_area.h > inner.h:
                # Widget is too tall: just align top
                if focus_area.top < inner.top:
                    scroll.y = inner.top - focus_area.top
            else:
                if focus_area.top < inner.top:
                    scroll.y = inner.top - focus_area.top
                elif focus_area.bottom > inner.bottom:
                    scroll.y = inner.bottom - focus_area.bottom

            # Apply
            self.parent.scroll_by(-scroll)

        # stop at root
        if self.parent.is_root:
            return

        # recurse upwards if parent has a layout
        if hasattr(self.parent.parent, "layout"):
            self.parent.parent.layout.scroll_to_widget(widget,focus_area)

    def handle_event(self, event):
        pass


class FreeLayout(Layout):
    pass


class SingleAxisLayout(Layout):
    def set_alignment(self, alignment) -> Self:
        self.alignment = alignment
        self.mark_dirty()
        return self

    def focus_next_child(self,current=None):
        logger.debug(f"{self.parent=}")

        self.parent.focus_next_tab(current)

    def focus_prev_child(self,current=None):
        self.parent.focus_prev_tab(current)

    def handle_event(self, event):
        if not self.parent.get_layout_children() or not self.parent.children_has_focus():
            return
        current = [c for c in self.parent.get_interactive_children() if c.is_focused][0]
        keys = (pygame.K_RIGHT, pygame.K_LEFT) if self.axis == 0 else (pygame.K_DOWN, pygame.K_UP)
        if event.type == pygame.KEYDOWN and event.key in keys:
            (self.focus_next_child if event.key == keys[0] else self.focus_prev_child)(current)
            event.consumed = True


class Row(SingleAxisLayout):
    axis = 0

    def __init__(self, gap=0):
        super().__init__()
        self.gap = max(0, gap)


class Column(SingleAxisLayout):
    axis = 1

    def __init__(self, gap=0):
        super().__init__()
        self.gap = max(0, gap)
        self.alignment = bf.alignment.CENTERX

    def set_alignment(self, alignment):
        return super().set_alignment(bf.alignment.CENTERX if alignment == bf.alignment.CENTER else alignment)


class DoubleAxisLayout(Layout):
    pass


class Grid(DoubleAxisLayout):
    def __init__(self, rows, cols, gap=0):
        if rows <= 0 or cols <= 0:
            raise ValueError("Grid rows and columns must be positive")
        super().__init__()
        self.rows, self.cols, self.gap = rows, cols, max(0, gap)

    def _dimensions(self):
        count = len(self.parent.get_layout_children())
        return max(self.rows, (count + self.cols - 1) // self.cols), self.cols

    def _sizes(self, available, measure=False):
        rows, cols = self._dimensions()
        cell = (max(0, available[0] - (cols-1)*self.gap) / cols,
                max(0, available[1] - (rows-1)*self.gap) / rows)
        sizes = {}
        for child in self.parent.get_layout_children():
            size = child.measure(cell) if measure else child.constrain_size(child.desired_size, cell)
            if self.fill and not measure:
                size = tuple(c if isfinite(c) else s for c, s in zip(cell, size))
            sizes[child] = size
        return sizes

    def _extent(self, sizes):
        if not sizes:
            return (0, 0)
        rows, cols = self._dimensions()
        return (max(s[0] for s in sizes.values()) * cols + (cols-1)*self.gap,
                max(s[1] for s in sizes.values()) * rows + (rows-1)*self.gap)

    def _rects(self, inner, sizes):
        cell_w = max((s[0] for s in sizes.values()), default=0)
        cell_h = max((s[1] for s in sizes.values()), default=0)
        return {child: pygame.FRect(inner.x + (i % self.cols)*(cell_w+self.gap) - self.parent.scroll.x,
                                    inner.y + (i // self.cols)*(cell_h+self.gap) - self.parent.scroll.y, *sizes[child])
                for i, child in enumerate(self.parent.get_layout_children())}

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
            l[target_index].ask_focus()

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
            l[target_index].ask_focus()

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
            l[target_index].ask_focus()

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
            l[target_index].ask_focus()

    def handle_event(self, event):
        if (
            not self.parent.get_layout_children()
            or not self.parent.children_has_focus()
        ):
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



class RowFill(Row):
    fill = True


class ColumnFill(Column):
    fill = True


class GridFill(Grid):
    fill = True

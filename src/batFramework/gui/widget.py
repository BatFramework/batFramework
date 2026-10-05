from __future__ import annotations
from typing import TYPE_CHECKING, Self, Callable, Any
from collections.abc import Iterable
from math import isfinite, isnan
import batFramework as bf
import pygame

if TYPE_CHECKING:
    from .constraints.constraints import Constraint
    from .root import Root


class WidgetMeta(type):
    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        bf.gui.StyleManager().register_widget(obj)
        return obj


class Widget(bf.Drawable, metaclass=WidgetMeta):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs,surface_flags=pygame.SRCALPHA)
        self.set_convert_alpha(True)
        self.draw_layer = bf.Layer.HUD
        self.children: list["Widget"] = []
        self.constraints: list[Constraint] = []
        self.gui_layer: bf.gui.GuiLayer = bf.gui.GuiLayer.NORMAL
        self.parent: "Widget" = None
        self.do_sort_children = False
        self.clip_children: bool = True
        self.min_size: tuple[float, float] = (0, 0)
        self._requested_size = self.rect.size
        self.desired_size: tuple[float, float] = (0, 0)
        self.available_size: tuple[float, float] = (float("inf"), float("inf"))
        self._measure_size = None
        self._measured_offer: tuple[float, float] | None = None
        self._measured_parent_size: tuple[float, float] | None = None
        self._arranging = False
        self._arranged_input: tuple[float, float, float, float] | None = None
        self._arranged_parent: tuple | None = None
        self._arranged_state = None
        self.padding = (0, 0, 0, 0)
        self.dirty_surface: bool = True  # If true, will call paint before drawing
        self.dirty_shape: bool = True  # Preferred size or a descendant may have changed.
        self._shape_revision = 0
        self.dirty_arrange: bool = True  # Final placement or descendant geometry may have changed.

        self.tooltip_text: str | None = (
            None  # If not None, will display a text when hovered
        )
        self.is_root: bool = False
        self.autoresize_w, self.autoresize_h = (
            True,
            True,
        )  # If True, the widget will have dynamic size depending on its contents


    def set_min_size(self, size: tuple[float, float]) -> Self:
        if self.min_size != size:
            self.min_size = size
            self.dirty_surface = True
            self.mark_shape_dirty()
        return self

    def mark_shape_dirty(self) -> Self:
        """Invalidate this measurement and the ancestors that depend on it."""
        self._shape_revision += 1
        widget = self
        while widget is not None:
            widget.dirty_shape = True
            widget.dirty_arrange = True
            widget = widget.parent
        return self

    def mark_arrange_dirty(self) -> Self:
        """Invalidate placement without discarding measured sizes."""
        widget = self
        while widget is not None:
            widget.dirty_arrange = True
            widget = widget.parent
        return self


    def get_gui_layer(self) -> bf.gui.GuiLayer:
        return self.gui_layer


    def set_tooltip_text(self, text: str | None) -> Self:
        self.tooltip_text = text
        return self

    def show(self) -> Self:
        self.visit(lambda w: w.set_visible(True))
        return self

    def hide(self) -> Self:
        self.visit(lambda w: w.set_visible(False))
        return self

    def set_visible(self, value):
        if self.visible != value:
            self.dirty_surface = True
            self.mark_shape_dirty()
        return super().set_visible(value)

    def kill(self):
        if self.parent:
            self.parent.remove(self)

        return super().kill()

    def set_clip_children(self, value: bool) -> Self:
        self.clip_children = value
        self.dirty_surface = True
        return self

    def __str__(self) -> str:
        return "Widget"

    def set_autoresize(self, value: bool) -> Self:
        # if (self.autoresize_w,self.autoresize_h) == (value,value):
        #     return self
        if (self.autoresize_w, self.autoresize_h) != (value, value):
            self.autoresize_w = self.autoresize_h = value
            self.dirty_surface = True
            self.mark_shape_dirty()
        return self

    def set_autoresize_w(self, value: bool) -> Self:
        if self.autoresize_w == value:
            return self
        self.autoresize_w = value
        self.dirty_surface = True
        self.mark_shape_dirty()
        return self

    def set_autoresize_h(self, value: bool) -> Self:
        if self.autoresize_h == value:
            return self
        self.autoresize_h = value
        self.dirty_surface = True
        self.mark_shape_dirty()
        return self

    def set_draw_order(self, draw_order: int) -> Self:
        bound_children = [c for c in self.children if c.draw_order == draw_order+1]
        super().set_draw_order(draw_order)
        if self.parent:
            self.parent.do_sort_children = True
        for child in bound_children:
            child.set_draw_order(draw_order+1)
        return self

    def expand_rect_with_padding(
        self, rect: pygame.typing.RectLike
    ) -> pygame.Rect | pygame.FRect:
        return pygame.FRect(
            rect[0] - self.padding[0],
            rect[1] - self.padding[1],
            rect[2] + self.padding[0] + self.padding[2],
            rect[3] + self.padding[1] + self.padding[3],
        )

    def set_position(self, x=None, y=None) -> Self:
        if x is None:
            x = self.rect.x
        if y is None:
            y = self.rect.y
        if (x, y) == self.rect.topleft:
            return self
        if not self._is_arranging_tree():
            self.mark_arrange_dirty()
        dx, dy = x - self.rect.x, y - self.rect.y
        self.rect.topleft = x, y
        _ = [c.set_position(c.rect.x + dx, c.rect.y + dy) for c in self.children]
        return self

    def set_center(self, x=None, y=None) -> Self:
        if x is None:
            x = self.rect.centerx
        if y is None:
            y = self.rect.centery
        if (x, y) == self.rect.center:
            return self
        if not self._is_arranging_tree():
            self.mark_arrange_dirty()
        dx, dy = x - self.rect.centerx, y - self.rect.centery
        self.rect.center = x, y
        _ = [
            c.set_center(c.rect.centerx + dx, c.rect.centery + dy)
            for c in self.children
        ]

        return self

    def _is_arranging_tree(self) -> bool:
        widget = self
        while widget is not None:
            if widget._arranging:
                return True
            widget = widget.parent
        return False

    def get_camera(self) -> bf.Camera | None:
        # children are drawn by their parent, so they share its camera
        if self.parent is not None:
            return self.parent.get_camera()
        return super().get_camera()

    def set_parent_scene(self, parent_scene: bf.Scene | None) -> Self:
        super().set_parent_scene(parent_scene)
        if parent_scene is None and self.parent_scene != None:
            bf.gui.StyleManager().remove_widget(self)

        for c in self.children:
            c.set_parent_scene(parent_scene)
        return self

    def set_parent(self, parent: "Widget") -> Self:
        if parent == self.parent:
            return self
        # if self.parent is not None and self.parent != parent:
        #     self.parent.remove(self)
        self.parent = parent
        self.mark_shape_dirty()
        self.visit(lambda w : w.set_draw_order(w.parent.draw_order + 1) if w.parent else None,top_down=True,include_self=True)
        return self

    def set_padding(self, value: float | int | tuple | list) -> Self:
        previous = self.padding
        if isinstance(value, Iterable):
            if len(value) > 4:
                pass
            elif any(v < 0 for v in value):
                pass
            elif len(value) == 2:
                self.padding = (value[0], value[1], value[0], value[1])
            else:
                self.padding = (*value, *self.padding[len(value) :])
        else:
            self.padding = (value,) * 4

        if self.padding != previous:
            self.dirty_surface = True
            self.mark_shape_dirty()
        return self

    def get_inner_rect(self) -> pygame.FRect:
        return self.get_local_inner_rect().move(self.rect.topleft)

    def get_local_inner_rect(self) -> pygame.FRect:
        return pygame.FRect(
            self.padding[0],
            self.padding[1],
            max(0, self.rect.w - self.padding[2] - self.padding[0]),
            max(0, self.rect.h - self.padding[1] - self.padding[3]),
        )

    def get_min_required_size(self) -> tuple[float, float]:
        return self.compute_min_size(self._requested_size)

    @staticmethod
    def _validate_size(size, *, finite=False):
        width, height = map(float, size)
        if any(isnan(v) or v < 0 or (finite and not isfinite(v)) for v in (width, height)):
            raise ValueError("Layout sizes must be non-negative (arranged sizes must be finite)")
        return width, height

    def get_content_size(self, size):
        """Space inside padding and relief, independent of the current rect."""
        return (max(0, size[0] - self.padding[0] - self.padding[2]),
                max(0, size[1] - self.padding[1] - self.padding[3] - getattr(self, "relief", 0)))

    def constrain_size(self, preferred, available):
        """Apply pure size policies, then enforce the parent's hard maximum.

        Higher priorities win; later constraints win ties. Custom size
        constraints implement Constraint.constrain_size during measurement.
        """
        size = self.compute_min_size(preferred)
        for constraint in sorted(self.constraints, key=lambda c: c.priority):
            if constraint.affects_size:
                size = constraint.constrain_size(self, size, available)
        return tuple(max(0, min(value, limit)) for value, limit in zip(size, available))

    def measure(self, available_size: tuple[float, float]) -> tuple[float, float]:
        """Receive a maximum and return a preference without changing geometry.

        Infinity is supported for unbounded axes (e.g. scrolling content).
        Padding belongs to this widget's size, not the offered child space.
        """
        offer = self._validate_size(available_size)
        parent_size = ((self.parent._measure_size or self.parent.rect.size)
                       if self.parent is not None else None)
        if (not self.dirty_shape and offer == self._measured_offer
                and parent_size == self._measured_parent_size):
            return self.desired_size
        self.available_size = offer
        limits = list(self.constrain_size(self.available_size, self.available_size))
        for axis, auto in enumerate((self.autoresize_w, self.autoresize_h)):
            if not auto:
                limits[axis] = min(limits[axis], max(self.min_size[axis], self._requested_size[axis]))
        # Explicit constraints can override a fixed preferred size.
        self._measure_size = self.constrain_size(limits, self.available_size)
        try:
            preferred = self.measure_override(self.get_content_size(self._measure_size))
            preferred = tuple(preferred[i] if auto else self._requested_size[i]
                              for i, auto in enumerate((self.autoresize_w, self.autoresize_h)))
            self.desired_size = self.constrain_size(preferred, self.available_size)
        finally:
            self._measure_size = None
        self._measured_offer = offer
        self._measured_parent_size = parent_size
        self.dirty_shape = False
        return self.desired_size

    def measure_override(self, available_size):
        """Override for intrinsic content; return the full size including padding."""
        for child in self.children:
            child.measure(available_size)
        return self.get_min_required_size()

    def constrain_position(self, proposed_rect) -> pygame.FRect:
        """Calculate final placement against the parent's arranged bounds.

        Pure position hooks run from low to high priority, in insertion order
        for ties. The returned rectangle keeps the parent's assigned size.
        """
        rect = pygame.FRect(proposed_rect)
        if self.parent is None:
            return rect
        assigned_size = rect.size
        outer = self.parent.rect.copy()
        inner = self.parent.get_inner_rect()
        for constraint in sorted(self.constraints, key=lambda c: c.priority):
            if not constraint.affects_position:
                continue
            rect = pygame.FRect(constraint.constrain_position(rect.copy(), outer.copy(), inner.copy()))
            if rect.size != assigned_size:
                raise ValueError(f"{constraint.name}: position constraints must preserve the assigned size")
            if not all(isfinite(value) for value in rect.topleft):
                raise ValueError(f"{constraint.name}: position constraints must return finite coordinates")
        return rect

    def arrange(self, final_rect) -> None:
        """Accept an exact (width, height) or world-space (x, y, width, height).

        The parent's allocation is authoritative, even below our minimum.
        arrange_override() positions content and descendants using that size.
        """
        if len(final_rect) == 2:
            final_rect = (*self.rect.topleft, *final_rect)
        rect = pygame.FRect(final_rect)
        self._validate_size(rect.size, finite=True)
        assigned = tuple(rect)
        parent_bounds = None
        if self.parent is not None and any(c.affects_position for c in self.constraints):
            parent_bounds = (tuple(self.parent.rect), tuple(self.parent.get_inner_rect()))
        state = self.get_arrangement_state()
        if (not self.dirty_arrange and assigned == self._arranged_input
                and parent_bounds == self._arranged_parent
                and state == self._arranged_state):
            return
        rect = self.constrain_position(rect)
        # Mutations made inside arrange_override remain pending for the next
        # update; this pass clears only the invalidation it is handling now.
        self.dirty_arrange = False
        self._arranging = True
        try:
            self.set_position(*rect.topleft)
            if self.rect.size != rect.size:
                self.dirty_surface = True
            self.rect.size = rect.size
            self.arrange_override()
            self._arranged_input = assigned
            self._arranged_parent = parent_bounds
            self._arranged_state = state
        except Exception:
            self.dirty_arrange = True
            raise
        finally:
            self._arranging = False

    def get_arrangement_state(self):
        """Additional mutable placement inputs, beyond the assigned rectangle."""
        return None

    def arrange_override(self):
        self.arrange_children()

    def arrange_children(self, exclude=()):
        """Arrange ordinary children; composites exclude their owned slots."""
        inner = self.get_content_size(self.rect.size)
        for child in self.children:
            if child not in exclude:
                size = child.constrain_size(child.desired_size, inner)
                child.arrange((*child.rect.topleft, *size))

    def compute_min_size(self, requested_size: tuple[float, float]) -> tuple[float, float]:
        return max(self.min_size[0], requested_size[0]), max(self.min_size[1], requested_size[1])

    def get_inner_width(self) -> float:
        return max(0, self.rect.w - self.padding[0] - self.padding[2])

    def get_inner_height(self) -> float:
        return max(0, self.rect.h - self.padding[1] - self.padding[3])

    def get_inner_left(self) -> float:
        return self.rect.left + self.padding[0]

    def get_inner_right(self) -> float:
        return self.rect.right - self.padding[2]

    def get_inner_center(self) -> tuple[float, float]:
        return self.get_inner_rect().center

    def get_inner_top(self) -> float:
        return self.rect.y + self.padding[1]

    def get_inner_bottom(self) -> float:
        return self.rect.bottom - self.padding[3]

    def get_debug_outlines(self):
        if self.visible:
            if any(self.padding):
                yield (self.get_inner_rect(), self.debug_color)
            # else:
            yield (self.rect, self.debug_color)
        for child in self.children:
            yield from child.get_debug_outlines()

    def add_constraints(self, *constraints: "Constraint") -> Self:
        # Add constraints without duplicates
        existing_names = {c.name for c in self.constraints}
        new_constraints = [c for c in constraints if c.name not in existing_names]
        self.constraints.extend(new_constraints)
        for constraint in new_constraints:
            constraint.add_owner(self)
        if new_constraints:
            self.mark_shape_dirty()

        return self

    def remove_constraints(self, *names: str) -> Self:
        removed = [c for c in self.constraints if c.name in names]
        self.constraints = [c for c in self.constraints if c.name not in names]
        for constraint in removed:
            constraint.remove_owner(self)
        if removed:
            self.mark_shape_dirty()

        return self



    def has_constraint(self, name: str) -> bool:
        return any(c.name == name for c in self.constraints)

    def get_root(self) -> "Root":
        if self.is_root:
            return self
        if self.parent:
            return self.parent.get_root()
        return None

    def get_by_tags(self, *tags: str) -> list["Widget"]:
        # use self.has_tags(*tags) for check
        result = []
        self.visit(lambda w: result.append(w) if w.has_tags(*tags) else None)
        return result

    def top_at(self, x: float | int, y: float | int) -> "None|Widget":
        for child in reversed(self.children):
            if child.visible:
                r = child.top_at(x, y)
                if r is not None:
                    return r

        return self if self.visible and self.rect.collidepoint(x, y) else None

    def add(self, *children: "Widget") -> Self:
        self.children.extend(children)
        for child in children:
            if child.parent is None:
                child.set_draw_order(self.draw_order+1)
            child.set_parent(self)
            child.set_parent_scene(self.parent_scene)
        self.dirty_surface = True
        if children:
            self.mark_shape_dirty()
        if self.parent:
            self.parent.do_sort_children = True
        return self

    def remove(self, *children: "Widget") -> Self:
        for child in self.children.copy():
            if child in children:
                child.set_parent(None)
                child.set_parent_scene(None)
                self.children.remove(child)
        if self.parent:
            self.parent.do_sort_children = True
        self.dirty_surface = True
        if children:
            self.mark_shape_dirty()
        return self

    def set_size(self, size: tuple) -> Self:
        if self._arranging:
            return self  # arrangement hooks cannot replace the parent's allocation
        previous = self._requested_size
        size = self._validate_size(tuple(previous[i] if v is None else v for i, v in enumerate(size)), finite=True)
        self._requested_size = tuple(size)
        if self._requested_size != previous:
            self.mark_shape_dirty()
        if size[0] == self.rect.w and size[1] == self.rect.h:
            return self
        self.rect.size = size
        self.dirty_surface = True
        return self

    def process_event(self, event: pygame.Event) -> None:
        # First propagate to children
        for child in self.children:
            child.process_event(event)
        super().process_event(event)

    def update(self, dt) -> None:
        if self.do_sort_children:
            self.children.sort(key=lambda c: c.draw_order)
            self.do_sort_children = False
        _ = [c.update(dt) for c in self.children]
        super().update(dt)

    def _resize_surface(self) -> bool:
        """
        returns True if size changed
        """
        new_size = tuple(map(int, self.rect.size))
        if self.surface.get_size() == new_size:
            return False

        old_alpha = self.surface.get_alpha()
        new_size = [max(0, i) for i in new_size]
        self.surface = pygame.Surface(new_size, self.surface_flags)
        if self.convert_alpha:
            self.surface = self.surface.convert_alpha()
        self.surface.set_alpha(old_alpha)
        return True

    def paint(self) -> None:
        self._resize_surface()
        self.surface.fill((0, 0, 0, 0))

    def visit(
        self,
        func: Callable[["Widget"], Any],
        *args,
        top_down: bool = True,
        include_self: bool = True,
        **kwargs,
    ) -> None:
        def _call(f, w):
            if args and kwargs:
                return f(w, *args, **kwargs)
            if args:
                return f(w, *args)
            if kwargs:
                return f(w, **kwargs)
            return f(w)

        if include_self and top_down:
            _call(func, self)
        for child in self.children:
            # pass top_down as a keyword to avoid it being treated as a positional arg
            child.visit(func, *args, top_down=top_down, **kwargs)
        if include_self and not top_down:
            _call(func, self)

    def visit_up(self, func, *args, include_self: bool = True, **kwargs) -> None:
        def _call(f, w):
            if args and kwargs:
                return f(w, *args, **kwargs)
            if args:
                return f(w, *args)
            if kwargs:
                return f(w, **kwargs)
            return f(w)

        if include_self:
            if _call(func, self):
                return
        if self.parent:
            self.parent.visit_up(func, *args, **kwargs)

    def set_convert_alpha(self, value):
        if value != self.convert_alpha:
            self.dirty_surface = True
        return super().set_convert_alpha(value)

    def set_surface_flags(self, surface_flags):
        if surface_flags != self.surface_flags:
            self.dirty_surface = True
        return super().set_surface_flags(surface_flags)

    def needs_paint(self) -> bool:
        """Whether this widget's surface needs repainting this frame."""
        return self.visible and self.dirty_surface

    def paint_tree(self):
        """Paint after arrangement, children first for composite surfaces."""
        for child in self.children:
            child.paint_tree()
        if self.needs_paint():
            self.paint()
            self.dirty_surface = False

    def draw(self, camera: bf.Camera) -> None:
        # Draw widget and handle clipping if necessary
        super().draw(camera)

        if self.clip_children:
            new_clip = camera.world_to_screen(self.get_inner_rect())
            old_clip = camera.surface.get_clip()
            new_clip = new_clip.clip(old_clip)
            camera.surface.set_clip(new_clip)

        # Draw each child widget, sorted by render order
        for child in self.children:
            if (not self.clip_children) or (
                child.rect.colliderect(self.rect) or not child.rect
            ):
                child.draw(camera)
        if self.clip_children:
            camera.surface.set_clip(old_clip)

from __future__ import annotations
from typing import TYPE_CHECKING, Self, Callable, Any
from collections.abc import Iterable
import batFramework as bf
import pygame

if TYPE_CHECKING:
    from .constraints.constraints import Constraint
    from .root import Root

from typing import Literal

MAX_ITERATIONS = 10
ResolveMode = Literal["all", "size", "position"]



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
        self.padding = (0, 0, 0, 0)
        self.dirty_surface: bool = True  # If true, will call paint before drawing
        self.dirty_shape: bool = True  # If true, will call (build+paint) before drawing
        self.dirty_position_constraints: bool = True  # Flag for position-related constraints
        self.dirty_size_constraints: bool = True  # Flag for size-related constraints

        self.tooltip_text: str | None = (
            None  # If not None, will display a text when hovered
        )
        self.is_root: bool = False
        self.autoresize_w, self.autoresize_h = (
            True,
            True,
        )  # If True, the widget will have dynamic size depending on its contents

        self._resolving_constraints: bool = False                 # re-entrancy guard
        self._constraints_to_ignore: list[Constraint] = []
        self._last_constraint_priorities: list[int] = []          # for change detection
        self._last_resolved: list[tuple[Constraint, int]] = []    # debug snapshot

    def set_min_size(self, size: tuple[float, float]) -> Self:
        self.min_size = size
        self.dirty_shape = True
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
        if self.visible != value and value == True:
            self.dirty_surface = True
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
        self.autoresize_w = self.autoresize_h = value
        self.dirty_shape = True
        return self

    def set_autoresize_w(self, value: bool) -> Self:
        if self.autoresize_w == value:
            return self
        self.autoresize_w = value
        self.dirty_shape = True
        return self

    def set_autoresize_h(self, value: bool) -> Self:
        if self.autoresize_h == value:
            return self
        self.autoresize_h = value
        self.dirty_shape = True
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
        dx, dy = x - self.rect.x, y - self.rect.y
        self.rect.topleft = x, y
        _ = [c.set_position(c.rect.x + dx, c.rect.y + dy) for c in self.children]
        self.dirty_position_constraints: bool = True
        return self

    def set_center(self, x=None, y=None) -> Self:
        if x is None:
            x = self.rect.centerx
        if y is None:
            y = self.rect.centery
        if (x, y) == self.rect.center:
            return self
        dx, dy = x - self.rect.centerx, y - self.rect.centery
        self.rect.center = x, y
        _ = [
            c.set_center(c.rect.centerx + dx, c.rect.centery + dy)
            for c in self.children
        ]
        self.dirty_position_constraints: bool = True

        return self

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
        self.visit(lambda w : w.set_draw_order(w.parent.draw_order + 1) if w.parent else None,top_down=True,include_self=True)
        return self

    def set_padding(self, value: float | int | tuple | list) -> Self:
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

        self.dirty_shape = True
        return self

    def get_inner_rect(self) -> pygame.FRect:
        r = self.rect.inflate(
            -self.padding[0] - self.padding[2], -self.padding[1] - self.padding[3]
        )
        return r

    def get_local_inner_rect(self) -> pygame.FRect:
        return pygame.FRect(
            self.padding[0],
            self.padding[1],
            self.rect.w - self.padding[2] - self.padding[0],
            self.rect.h - self.padding[1] - self.padding[3],
        )

    def get_min_required_size(self) -> tuple[float, float]:
        return self.compute_min_size(self.rect.size)

    def compute_min_size(self, requested_size: tuple[float, float]) -> tuple[float, float]:
        return max(self.min_size[0], requested_size[0]), max(self.min_size[1], requested_size[1])

    def get_inner_width(self) -> float:
        return self.rect.w - self.padding[0] - self.padding[2]

    def get_inner_height(self) -> float:
        return self.rect.h - self.padding[1] - self.padding[3]

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

        # Sort constraints by priority
        self.constraints.sort(key=lambda c: c.priority)

        # Update dirty flags based on the new constraints
        if any(c.affects_size for c in new_constraints):
            self.dirty_size_constraints = True
        if any(c.affects_position for c in new_constraints):
            self.dirty_position_constraints = True

        # Clear ignored constraints
        self._constraints_to_ignore = []

        return self

    def remove_constraints(self, *names: str) -> Self:
        for c in self.constraints:
            if c.name in names:
                c.on_removal(self)
        self.constraints = [c for c in self.constraints if c.name not in names]
        self._constraints_to_ignore = []
        self.dirty_size_constraints = True
        self.dirty_position_constraints = True

        return self



    def resolve_constraints(self, mode: ResolveMode = "all") -> None:
        """
        Resolve constraints affecting size, position, or both.

        Iterates until a stable solution is found, MAX_ITERATIONS is reached,
        or oscillation is detected.
        """
        if self.parent is None or not self.constraints:
            self._clear_constraint_dirty(mode)
            return

        # Re-entrancy guard. If a constraint's apply() triggers another
        # resolve on the same widget, bail rather than corrupt state.
        if self._resolving_constraints:
            return
        self._resolving_constraints = True

        try:
            # If priorities changed since last call, the ignore list is stale.
            current_priorities = [c.priority for c in self.constraints]
            if current_priorities != self._last_constraint_priorities:
                self._last_constraint_priorities = current_priorities
                self._constraints_to_ignore = []

            # Filter to relevant constraints, highest priority first.
            if mode == "size":
                relevant = [c for c in self.constraints if c.affects_size]
            elif mode == "position":
                relevant = [c for c in self.constraints if c.affects_position]
            else:
                relevant = list(self.constraints)
            relevant.sort(key=lambda c: c.priority, reverse=True)

            resolved: dict[int, Constraint] = {}   # id -> constraint
            seen_states: set[frozenset[int]] = set()
            iteration = 0
            converged = False

            for iteration in range(1, MAX_ITERATIONS + 1):
                changed = False

                # Phase 1: drop previously-resolved constraints that broke.
                for cid, c in list(resolved.items()):
                    if not c.evaluate(self.parent, self):
                        del resolved[cid]
                        changed = True

                # Phase 2: try to apply unresolved constraints.
                for c in relevant:
                    if id(c) in resolved:
                        continue
                    if c.apply(self.parent, self):
                        resolved[id(c)] = c
                        changed = True

                if not changed:
                    converged = True
                    break

                state = frozenset(resolved.keys())
                if state in seen_states:
                    break
                seen_states.add(state)

            if not converged:
                self._constraints_to_ignore += [
                    c for c in relevant if id(c) not in resolved
                ]

            self._last_resolved = [(c, iteration) for c in resolved.values()]
            self._clear_constraint_dirty(mode)
        finally:
            self._resolving_constraints = False


    def _clear_constraint_dirty(self, mode: ResolveMode) -> None:
        if mode in ("size", "all"):
            self.dirty_size_constraints = False
        if mode in ("position", "all"):
            self.dirty_position_constraints = False     
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

    def resolve_size(self, target_size):
        return self.compute_min_size((
            target_size[0] if self.autoresize_w else self.rect.w,
            target_size[1] if self.autoresize_h else self.rect.h,
        ))

    def set_size(self, size: tuple) -> Self:
        size = list(size)
        if size[0] is None:
            size[0] = self.rect.w
        if size[1] is None:
            size[1] = self.rect.h
        if size[0] == self.rect.w and size[1] == self.rect.h:
            return self
        self.rect.size = size
        self.dirty_shape = True
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

    def build(self) -> bool:
        """
        Updates the size of the widget.
        return True if size changed
        """
        return False

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

    """
    1 : 
    bottom up -> only build children

    """



    def find_highest_dirty_constraints_widget(self) -> "Widget":
        if self.is_root : return self
        w = self.parent
        tmp = w
        while not tmp.is_root:
            if tmp.dirty_size_constraints or tmp.dirty_shape or tmp.autoresize_h or tmp.autoresize_w:
                w = tmp
            if not tmp.parent:
                break
            tmp = tmp.parent
        return w

    def set_convert_alpha(self, value):
        if value != self.convert_alpha:
            self.dirty_surface = True
        return super().set_convert_alpha(value)

    def set_surface_flags(self, surface_flags):
        if surface_flags != self.surface_flags:
            self.dirty_surface = True
        return super().set_surface_flags(surface_flags)

    def apply_updates(self, pass_type : Literal["pre","post"]):
        # print(f"Apply updates {pass_type} called on {self}")
        if pass_type == "pre":
            self.apply_pre_updates()
            for child in self.children:
                child.apply_updates("pre")
        elif pass_type == "post":
            for child in self.children:
                child.apply_updates("post")
            self.apply_post_updates(skip_draw=not self.visible)

    def apply_pre_updates(self):
        """
        TOP TO BOTTOM
        Resolves size-related constraints before propagating updates to children.
        """
        if self.dirty_size_constraints:
            self.resolve_constraints(mode = "size")
            self.dirty_size_constraints = False
            self.dirty_position_constraints = True

    def apply_post_updates(self, skip_draw: bool = False):
        """
        BOTTOM TO TOP
        Resolves position-related constraints after propagating updates from children.
        """

        if self.dirty_shape:
            clear_dirty_shape = True
            if self.build():
                self.dirty_size_constraints = True
                self.dirty_position_constraints = True
                ancestor = self.find_highest_dirty_constraints_widget()
                if ancestor:
                    ancestor.dirty_shape = True
                    # trigger layout or constraint updates in parent
                    from .container import Container
                    from .scrollingContainer import ScrollingContainer

                    if ancestor and (
                        (isinstance(ancestor, Container)
                        and (ancestor.autoresize_h or ancestor.autoresize_w))
                        or isinstance(ancestor, ScrollingContainer)
                    ):
                        
                        ancestor.dirty_layout = True
                        clear_dirty_shape = False
            self.dirty_shape = False if clear_dirty_shape else True
            self.dirty_surface = True

        if self.dirty_position_constraints:
            self.resolve_constraints(mode = "position")

        if self.dirty_surface and not skip_draw:
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

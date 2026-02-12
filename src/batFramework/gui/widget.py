from __future__ import annotations
from typing import TYPE_CHECKING, Self, Callable, Any
from collections.abc import Iterable
import batFramework as bf
import pygame

if TYPE_CHECKING:
    from .constraints.constraints import Constraint
    from .root import Root

MAX_ITERATIONS = 10

class WidgetMeta(type):
    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        bf.gui.StyleManager().register_widget(obj)
        return obj


class Widget(bf.Drawable, metaclass=WidgetMeta):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.children: list["Widget"] = []
        self.constraints: list[Constraint] = []
        self.parent: "Widget" = None
        self.do_sort_children = False
        self.clip_children: bool = True
        self.padding = (0, 0, 0, 0)
        self.dirty_surface: bool = True  # If true, will call paint before drawing
        self.dirty_shape: bool = True  # If true, will call (build+paint) before drawing
        self.dirty_position_constraints: bool = True  # Flag for position-related constraints
        self.dirty_size_constraints: bool = True  # Flag for size-related constraints

        self.tooltip_text: str | None = None  # If not None, will display a text when hovered
        self.is_root: bool = False
        self.autoresize_w, self.autoresize_h = True, True  # If True, the widget will have dynamic size depending on its contents
        self._constraint_iteration = 0
        self._constraints_to_ignore: list[Constraint] = []
        self._constraints_capture: list[Constraint] = []

    def set_tooltip_text(self,text:str|None)->Self:
        self.tooltip_text = text
        return self

    def show(self) -> Self:
        self.visit(lambda w: w.set_visible(True))
        return self

    def hide(self) -> Self:
        self.visit(lambda w: w.set_visible(False))
        return self

    def set_visible(self, value):
        if self.visible != value and value==True:
            self.dirty_surface = True
        return super().set_visible(value)

    def kill(self):
        if self.parent:
            self.parent.remove(self)
        if self.parent_scene and self.parent_layer is not None:
            self.parent_scene.remove(self.parent_layer.name,self)
            
        return super().kill()

    def set_clip_children(self, value: bool) -> Self:
        self.clip_children = value
        self.dirty_surface = True
        return self

    def __str__(self) -> str:
        return "Widget"

    def set_autoresize(self, value: bool) -> Self:
        self.autoresize_w = self.autoresize_h = value
        self.dirty_shape = True
        return self

    def set_autoresize_w(self, value: bool) -> Self:
        self.autoresize_w = value
        self.dirty_shape = True
        return self

    def set_autoresize_h(self, value: bool) -> Self:
        self.autoresize_h = value
        self.dirty_shape = True
        return self

    def set_render_order(self, render_order: int) -> Self:
        super().set_render_order(render_order)
        if self.parent:
            self.parent.do_sort_children = True
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

    def set_parent_scene(self, parent_scene: bf.Scene | None) -> Self:
        super().set_parent_scene(parent_scene)
        if parent_scene is None and self.parent_scene != None:
            bf.gui.StyleManager().remove_widget(self)

        for c in self.children:
            c.set_parent_scene(parent_scene)
        return self

    def set_parent_layer(self, layer):
        super().set_parent_layer(layer)
        for c in self.children:
            c.set_parent_layer(layer)
        return self

    def set_parent(self, parent: "Widget") -> Self:
        if parent == self.parent:
            return self
        # if self.parent is not None and self.parent != parent:
        #     self.parent.remove(self)
        self.parent = parent
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

    def get_local_inner_rect(self)->pygame.FRect:
        return pygame.FRect(
            self.padding[0],
            self.padding[1],
            self.rect.w - self.padding[2] - self.padding[0],
            self.rect.h - self.padding[1] - self.padding[3],
        )

    def get_min_required_size(self) -> tuple[float, float]:
        return self.rect.size

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
        self.dirty_position_constraints= True

        return self


    def resolve_constraints(self, size_only: bool = False, position_only: bool = False) -> None:
        """
        Resolve constraints affecting size and/or position independently.

        This system attempts to apply constraints iteratively until a stable solution is found,
        or until MAX_ITERATIONS is reached.
        """
        if self.parent is None or not self.constraints:
            if size_only:
                self.dirty_size_constraints = False
            if position_only:
                self.dirty_position_constraints = False
            return

        # If not currently resolving constraints, reset tracking lists
        if not self._constraint_iteration:
            self._constraints_capture = []
        else:
            # Detect constraint priority changes since last resolution
            current_priorities = [c.priority for c in self.constraints]
            if current_priorities != self._constraints_capture:
                self._constraints_capture = current_priorities
                self._constraints_to_ignore = []

        # Filter constraints based on what needs resolving
        def is_relevant(c: "Constraint") -> bool:
            return (
                c.affects_size if size_only else
                c.affects_position if position_only else
                True
            )

        active_constraints = [c for c in self.constraints if is_relevant(c)]
        active_constraints.sort(key=lambda c: c.priority, reverse=True)

        resolved = []
        for iteration in range(MAX_ITERATIONS):
            self._constraint_iteration += 1
            changed = False

            for constraint in active_constraints:
                if constraint in resolved:
                    # Re-evaluate to confirm the constraint is still satisfied
                    if not constraint.evaluate(self.parent, self):
                        resolved.remove(constraint)
                        changed = True
                else:
                    # Try applying unresolved constraint
                    if constraint.apply(self.parent, self):
                        resolved.append(constraint)
                        changed = True

            if not changed:
                break  # All constraints stable — done

        # If solution is still unstable, record the unresolved ones
        if self._constraint_iteration >= MAX_ITERATIONS:
            self._constraints_to_ignore += [
                c for c in active_constraints if c not in resolved
            ]

        # Record final resolved constraints for debugging/tracking
        self._constraints_capture.clear()
        self._constraints_capture.extend(
            (c, self._constraint_iteration) for c in resolved
        )

        # Clear appropriate dirty flags
        if size_only:
            self.dirty_size_constraints = False
        if position_only:
            self.dirty_position_constraints = False

        # Debug print for ignored constraints
        # if self._constraints_to_ignore:
            # print(f"{self} ignored constraints: {[str(c) for c in self._constraints_to_ignore]}")


    def has_constraint(self, name: str) -> bool:
        return any(c.name == name for c in self.constraints)

    def get_root(self) -> "Root":
        if self.is_root:
            return self
        if self.parent:
            return self.parent.get_root()
        return None

    def get_by_tags(self,*tags: str)->list["Widget"]:
        #use self.has_tags(*tags) for check
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
        i = len(self.children)
        for child in children:
            if child.render_order == 0:
                child.set_render_order(i+1)
            child.set_parent(self)
            child.set_parent_layer(self.parent_layer)
            child.set_parent_scene(self.parent_scene)
            i += 1
        if self.parent:
            self.parent.do_sort_children = True
        return self

    def remove(self, *children: "Widget") -> Self:
        for child in self.children.copy():
            if child in children:
                child.set_parent(None)
                child.set_parent_scene(None)
                child.set_parent_layer(None)
                self.children.remove(child)
        if self.parent:
            self.parent.do_sort_children = True

    def resolve_size(self, target_size):
        return (
            target_size[0] if self.autoresize_w else self.rect.w,
            target_size[1] if self.autoresize_h else self.rect.h
        )

    def set_size(self, size: tuple) -> Self:
        size = list(size)
        if size[0] is None:
            size[0] = self.rect.w
        if size[1] is None:
            size[1] = self.rect.h
        if size[0] == self.rect.w and size[1] == self.rect.h : return self
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
            self.children.sort(key=lambda c: c.render_order)
            self.do_sort_children = False
        _ = [c.update(dt) for c in self.children]
        super().update(dt)


    def _resize_surface(self)->bool:
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

    def visit(self, func: Callable[["Widget"], Any], *args, top_down: bool = True,include_self:bool=True, **kwargs) -> None:
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

    def visit_up(self, func, *args, include_self:bool = True, **kwargs) -> None:
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
    def update_children_size(self, widget: "Widget"):
        # print(widget,widget.uid,"constraints resolve in update size func")

        widget.resolve_constraints()
        if widget.dirty_shape:
            # print(widget,widget.uid,"build in update size func")
            widget.build()
            widget.dirty_shape = False
            widget.dirty_surface = True

    def find_highest_dirty_constraints_widget(self) -> "Widget":
        w = self
        tmp = w
        while not tmp.is_root:
            if tmp.dirty_size_constraints or tmp.dirty_shape:
                w = tmp
            if not tmp.parent:
                break
            tmp = tmp.parent
        return w


    def apply_updates(self,pass_type):
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
            self.resolve_constraints(size_only=True)
            self.dirty_size_constraints = False
            self.dirty_position_constraints = True

    def apply_post_updates(self, skip_draw: bool = False):
        """
        BOTTOM TO TOP
        Resolves position-related constraints after propagating updates from children.
        """

        if self.dirty_shape:
            
            if self.build():
                self.dirty_size_constraints = True
                self.dirty_position_constraints = True
                if self.parent :
                # trigger layout or constraint updates in parent
                    from .container import Container
                    from .scrollingContainer import ScrollingContainer
                    if self.parent and (isinstance(self.parent, Container) and (self.parent.autoresize_h or self.parent.autoresize_w) \
                        or isinstance(self.parent,ScrollingContainer)):
                        self.parent.dirty_layout = True
                        self.parent.dirty_shape = True
            self.dirty_shape = False
            self.dirty_surface = True

        if self.dirty_position_constraints:
            self.resolve_constraints(position_only=True)

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
            if (not self.clip_children) or (child.rect.colliderect(self.rect) or not child.rect):
                child.draw(camera)
        if self.clip_children:
            camera.surface.set_clip(old_clip)

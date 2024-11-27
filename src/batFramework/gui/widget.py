from typing import TYPE_CHECKING, Self, Callable
from collections.abc import Iterable
import batFramework as bf
import pygame

if TYPE_CHECKING:
    from .constraints.constraints import Constraint
    from .root import Root
MAX_CONSTRAINTS = 10


class WidgetMeta(type):
    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)
        bf.StyleManager().register_widget(obj)
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
        self.dirty_surface: bool = True  #  if true will call paint before drawing
        self.dirty_shape: bool = True  #    if true will call (build+paint) before drawing
        self.dirty_constraints: bool = False # if true will call resolve_constraints

        self.is_root: bool = False
        self.autoresize_w, self.autoresize_h = True, True
        self.__constraint_iteration = 0
        self.__constraints_to_ignore = []
        self.__constraints_capture = None

    def show(self) -> Self:
        self.visit(lambda w: w.set_visible(True))
        return self

    def hide(self) -> Self:
        self.visit(lambda w: w.set_visible(False))
        return self

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

    def inflate_rect_by_padding(
        self, rect: pygame.Rect | pygame.FRect
    ) -> pygame.Rect | pygame.FRect:
        return pygame.FRect(
            rect[0] - self.padding[0],
            rect[1] - self.padding[1],
            rect[2] + self.padding[0] + self.padding[2],
            rect[3] + self.padding[1] + self.padding[3],
        )

    def set_position(self, x, y) -> Self:
        if x is None:
            x = self.rect.x
        if y is None:
            y = self.rect.y
        if (x, y) == self.rect.topleft:
            return self
        dx, dy = x - self.rect.x, y - self.rect.y
        self.rect.topleft = x, y
        _ = [c.set_position(c.rect.x + dx, c.rect.y + dy) for c in self.children]
        return self

    def set_center(self, x, y) -> Self:
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
        return self

    def set_parent_scene(self, parent_scene: bf.Scene | None) -> Self:
        super().set_parent_scene(parent_scene)
        if parent_scene is None:
            bf.StyleManager().remove_widget(self)

        for c in self.children:
            c.set_parent_scene(parent_scene)
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

    def get_padded_rect(self) -> pygame.FRect:
        r = self.rect.inflate(
            -self.padding[0] - self.padding[2], -self.padding[1] - self.padding[3]
        )
        # r.normalize()
        return r

    def get_min_required_size(self) -> tuple[float, float]:
        return self.rect.size

    def get_padded_width(self) -> float:
        return self.rect.w - self.padding[0] - self.padding[2]

    def get_padded_height(self) -> float:
        return self.rect.h - self.padding[1] - self.padding[3]

    def get_padded_left(self) -> float:
        return self.rect.left + self.padding[0]

    def get_padded_right(self) -> float:
        return self.rect.right + self.padding[2]

    def get_padded_center(self) -> tuple[float, float]:
        return self.get_padded_rect().center

    def get_padded_top(self) -> float:
        return self.rect.y + self.padding[1]

    def get_padded_bottom(self) -> float:
        return self.rect.bottom - self.padding[3]

    def get_debug_outlines(self):
        if self.visible:
            if any(self.padding):
                yield (self.get_padded_rect(), self.debug_color)
            else:
                yield (self.rect, self.debug_color)
        for child in self.children:
            yield from child.get_debug_outlines()

    def add_constraints(self, *constraints: "Constraint") -> Self:
        self.constraints.extend(constraints)
        seen = set()
        result = []
        for c in self.constraints:
            if not any(c == o for o in seen):
                result.append(c)
                seen.add(c.name)
        self.constraints = result
        self.constraints.sort(key=lambda c: c.priority)
        self.dirty_constraints = True
        self.__constraint_to_ignore = []

        return self


    def remove_constraints(self, *names: str) -> Self:
        for c in self.constraints:
            if c.name in names:
                c.on_removal(self)
        self.constraints = [c for c in self.constraints if c.name not in names]
        self.__constraint_to_ignore = []
        return self

    def resolve_constraints(self) -> None:
        if self.parent is None or not self.constraints:
            self.dirty_constraints = False
            return

        if not self.__constraint_iteration:
            self.__constraints_capture = None
        else:
            capture = tuple([c.priority for c in self.constraints])
            if capture != self.__constraints_capture:
                self.__constraints_capture = capture
                self.__constraint_to_ignore = []
                
        constraints = self.constraints.copy()
        # If all are resolved early exit
        if all(c.evaluate(self.parent,self) for c in constraints if c not in self.__constraint_to_ignore):
            self.dirty_constraints = False
            return
        
        # # Here there might be a conflict between 2 or more constraints
        # we have to determine which ones causes conflict and ignore the one with least priority

        stop = False

        while True:
            stop = True
            # first pass with 2 iterations to sort out the transformative constraints
            for _ in range(2):
                for c in constraints:
                    if c in self.__constraints_to_ignore:continue
                    if not c.evaluate(self.parent,self) :
                        # print(c," is applied")
                        c.apply(self.parent,self)
            # second pass where we check conflicts
            for c in constraints:
                if c in self.__constraints_to_ignore:
                    continue
                if not c.evaluate(self.parent,self):
                    # first pass invalidated this constraint
                    self.__constraints_to_ignore.append(c)
                    stop = False
                    break

            if stop: 
                break

        if self.__constraints_to_ignore:
            print("Constraints ignored : ",[str(c) for c in self.__constraints_to_ignore])
            
        self.dirty_constraints = False
        # print(self,self.uid,"resolve constraints : Success")


    def has_constraint(self, name: str) -> bool:
        return any(c.name == name for c in self.constraints)

    def get_root(self) -> "Root":
        if self.is_root:
            return self
        if self.parent:
            return self.parent.get_root()
        return None

    def top_at(self, x: float | int, y: float | int) -> "None|Widget":
        if self.children:
            for child in reversed(self.children):
                # if child.visible:
                r = child.top_at(x, y)
                if r is not None:
                    return r
        return self if  self.rect.collidepoint(x, y) else None

    def add(self, *children: "Widget") -> Self:
        self.children.extend(children)
        i = len(self.children)
        for child in children:

            child.set_render_order(i).set_parent(self).set_parent_scene(
                self.parent_scene
            )
            i += 1
        if self.parent:
            self.parent.do_sort_children = True
        return self

    def remove(self, *children: "Widget") -> Self:
        for child in self.children:
            if child in children:
                child.set_parent(None).set_parent_scene(None)
                self.children.remove(child)
        if self.parent:
            self.parent.do_sort_children = True

    def set_size_if_autoresize(self, size: tuple[float, float]) -> Self:
        size = list(size)
        size[0] = size[0] if self.autoresize_w else None
        size[1] = size[1] if self.autoresize_h else None
        self.set_size(size)
        return self

    def set_size(self, size: tuple) -> Self:
        size = list(size)
        if size[0] is None:
            size[0] = self.rect.w
        if size[1] is None:
            size[1] = self.rect.h
        if (int(size[0]),int(size[1])) == (int(self.rect.w),int(self.rect.h)):
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
            self.children.sort(key=lambda c: c.render_order)
            self.do_sort_children = False
        _ = [c.update(dt) for c in self.children]
        super().update(dt)

    def build(self) -> None:
        new_size = tuple(map(int, self.rect.size))
        if self.surface.get_size() != new_size:
            old_alpha = self.surface.get_alpha()
            new_size = [max(0, i) for i in new_size]
            self.surface = pygame.Surface(new_size, self.surface_flags)
            if self.convert_alpha:
                self.surface = self.surface.convert_alpha()
            self.surface.set_alpha(old_alpha)

    def paint(self) -> None:
        self.surface.fill((0, 0, 0, 0))
        return self

    def visit(self, func: Callable, top_down: bool = True, *args, **kwargs) -> None:
        if top_down:
            func(self, *args, **kwargs)
        for child in self.children:
            child.visit(func, top_down,*args,**kwargs)
        if not top_down:
            func(self, *args, **kwargs)

    def visit_up(self, func, *args, **kwargs) -> None:
        if func(self, *args, **kwargs):
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
            if tmp.dirty_constraints or tmp.dirty_shape:
                w = tmp
            if not tmp.parent:
                break
            tmp = tmp.parent
        return w


    def apply_updates(self) -> None:

        if self.dirty_constraints:
            self.resolve_constraints()  # Finalize positioning based on final size
            self.dirty_constraints = False

        # Build shape if needed
        if self.dirty_shape:
            self.build()  # Finalize widget size
            self.dirty_shape = False
            self.dirty_surface = True
            self.dirty_constraints = True
            # Propagate dirty_constraints to children in case size affects their position
            for child in self.children:
                child.dirty_constraints = True

        # Resolve constraints now that size is finalized
        if self.dirty_constraints:
            self.resolve_constraints()  # Finalize positioning based on final size
            self.dirty_constraints = False


        # Step 3: Paint the surface if flagged as dirty
        if self.dirty_surface:
            self.paint()
            self.dirty_surface = False
    


    def draw(self, camera: bf.Camera) -> None:
        self.apply_updates()
        # Draw widget and handle clipping if necessary
        super().draw(camera)

        if self.clip_children:
            new_clip = camera.world_to_screen(self.get_padded_rect())
            old_clip = camera.surface.get_clip()
            new_clip = new_clip.clip(old_clip)
            camera.surface.set_clip(new_clip)

        # Draw each child widget, sorted by render order
        for child in sorted(self.children, key=lambda c: c.render_order):
            child.draw(camera)

        if self.clip_children:
            camera.surface.set_clip(old_clip)

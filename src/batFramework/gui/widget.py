from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .constraints.constraints import Constraint
    from .root import Root
from typing import Self

import batFramework as bf
import pygame
from math import ceil

MAX_CONSTRAINT_ITERATION = 10

class Widget(bf.Entity):
    def __init__(self, convert_alpha=True,*args,**kwargs) -> None:
        super().__init__(convert_alpha=convert_alpha)
        self.autoresize = False # resize by internal methods (such as set_text) allowed
        self.parent: None | Self = None
        self.is_root: bool = False
        self.children: list["Widget"] = []
        self.focusable: bool = False # can get focus
        self.constraints: list[Constraint] = []
        self.clip_to_parent : bool = True
        self.alpha : int = 255
        self.surface.fill("white")
        self.set_debug_color("red")
        self.padding: tuple[float | int] = (0, 0, 0, 0)
        self.__recursive_constraint_count = 0

    def enable_clip_to_parent(self)->Self:
        self.clip_to_parent = True
        self.build()
        return self
    
    def disable_clip_to_parent(self)->Self:
        self.clip_to_parent = False
        self.build()
        return self

    def set_alpha(self,value: int,propagate:bool = True)->Self:
        self.alpha = value
        self.surface.set_alpha(value)
        if propagate and self.children:
            for c in self.children : c.propagate_function(lambda e : e.set_alpha(value))
        return self

    def get_alpha(self)->int:
        return self.surface.get_alpha()

    def set_visible(self,value : bool,propagate:bool=True)->Self:
        super().set_visible(value)
        if propagate: _ = [c.set_visible(value,propagate) for c in self.children]
        return self



    def set_padding(self, value: float | int | tuple | list) -> Self:
        old_raw_size = (
            self.rect.w - self.padding[0] - self.padding[2],
            self.rect.h - self.padding[1] - self.padding[3],
        )
        if isinstance(value, list) or isinstance(value, tuple):
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

        self.set_size((
            old_raw_size[0] + self.padding[0] + self.padding[2],
            old_raw_size[1] + self.padding[1] + self.padding[3]
        ))
        return self


    def inflate_rect_by_padding(self, rect: pygame.FRect) -> pygame.FRect:
        return pygame.FRect(
            rect[0] - self.padding[0],
            rect[1] - self.padding[1],
            rect[2] + self.padding[0] + self.padding[2],
            rect[3] + self.padding[1] + self.padding[3],
        )
    def get_min_required_size(self)->tuple[float,float]:
        return self.rect.size

    def get_padded_left(self) -> float:
        return self.rect.left + self.padding[0]

    def get_padded_top(self) -> float:
        return self.rect.top + self.padding[1]

    def get_padded_right(self) -> float:
        return self.rect.right - self.padding[2]

    def get_padded_bottom(self) -> float:
        return self.rect.bottom - self.padding[3]

    def get_padded_width(self) -> float:
        return self.rect.w - self.padding[0] - self.padding[2]

    def get_padded_height(self) -> float:
        return self.rect.h - self.padding[1] - self.padding[3]

    def get_padded_rect(self) -> pygame.FRect:
        return pygame.FRect(
            self.rect.left + self.padding[0],
            self.rect.top + self.padding[1],
            self.get_padded_width(),
            self.get_padded_height(),
        )

    def get_padded_rect_rel(self) -> pygame.FRect:
        return self.get_padded_rect().move(-self.rect.left, -self.rect.top)

    def get_padded_center(self) -> tuple[float, float]:
        return self.get_padded_rect().center

    def get_depth(self) -> int:
        if self.is_root or self.parent is None:
            return 0
        return self.parent.get_depth() + 1
        
    def top_at(self, x: float|int, y: float|int) -> "None|Widget":
        if self.visible and self.rect.collidepoint(x, y):
            if self.children:
                for child in reversed(self.children):
                    r = child.top_at(x, y)
                    if r is not None:
                        return r
            return self
        return None

    def get_constraint(self, name: str) -> Constraint | None:
        return next((c for c in self.constraints if c.name == name), None)

    def add_constraints(self, *constraints: Constraint) -> Self:
        for constraint in constraints:
            c = self.get_constraint(constraint.name)
            if c is not None:
                self.constraints.remove(c)
            self.constraints.append(constraint)
        self.apply_constraints()
        return self

    def has_constraint(self, name: str) -> bool:
        return any(c.name == name for c in self.constraints)

    def apply_all_constraints(self) -> None:
        for child in self.children:
            child.apply_all_constraints()
        self.apply_constraints()

    def apply_constraints(self) -> None:
        self.__recursive_constraint_count += 1
        if not self.parent:
            # print(f"Warning : can't apply constraints on {self.to_string()} without parent widget")
            return
        if not self.constraints:
            return
        # Sort constraints based on priority
        self.constraints.sort(key=lambda c: c.priority)

        for iteration in range(MAX_CONSTRAINT_ITERATION):
            unsatisfied = []  # Initialize a flag

            for constraint in self.constraints:
                if not constraint.evaluate(self.parent, self):
                    unsatisfied.append(constraint)
                    constraint.apply(self.parent, self)
            if not unsatisfied:
                #     data = ''.join(f"\n\t->{c.to_string()}" for c in self.constraints)
                #     print(self.get_depth()*'\t'+f"Following constraints of {self.to_string()} were all satisfied :{data}")
                self.__recursive_constraint_count = 0
                break
            # print(f"pass {iteration}/{max_iterations} : unsatisfied = {';'.join(c.to_string() for c in unsatisfied)}")
            if iteration >= MAX_CONSTRAINT_ITERATION - 1 or self.__recursive_constraint_count >= MAX_CONSTRAINT_ITERATION -1 :
                unsatisfied_constraints = '\n\t'.join([c.to_string() for c in unsatisfied])
                raise ValueError(
                    f"[WARNING] Following constraints for {self.to_string()} were not satisfied : \n{unsatisfied_constraints}"
                    )

    # GETTERS
    def get_by_tags(self, *tags :str):
        for c in self.children:
            yield from c.get_by_tags(*tags)
        if any(self.has_tags(t) for t in tags):
            yield self

    def count_children_recursive(self):
        return 1 + sum(child.count_children_recursive() for child in self.children)


    def propagate_function(self,function,bottom_up:bool = False):
        if not bottom_up : function(self)
        for child in self.children:
            child.propagate_function(function)
        if bottom_up: function(self)
        
    def get_root(self) -> Root | None:
        if self.parent_scene is not None:
            return self.parent_scene.root
        return None if self.parent is None else self.parent.get_root()

    def get_size_int(self) -> tuple[int, int]:
        return (max(0,ceil(self.rect.width)), max(0,ceil(self.rect.height)))

    def get_center(self) -> tuple[float, float]:
        return self.rect.center

    def get_bounding_box(self):            
        yield (self.rect, self.debug_color)
        yield (self.get_padded_rect(), "gray20")
        for child in self.children:
            yield from child.get_bounding_box()

    def set_autoresize(self, value: bool) -> Self:
        self.autoresize = value
        self.build()
        return self

    def set_parent(self, parent: Self | None) -> Self:
        if self.parent:
            self.parent.remove_child(self)
        self.parent = parent
        self.apply_all_constraints()
        return self

    # SETTERS

    def set_root(self) -> Self:
        self.is_root = True
        return self

    def set_parent_scene(self, scene) -> Self:
        super().set_parent_scene(scene)
        for child in self.children:
            child.set_parent_scene(scene)
        return self
    
    def set_x(self, x: float) -> Self:
        if x == self.rect.x : return self
        delta = x - self.rect.x
        self.rect.x = x
        for child in self.children:
            child.set_x(child.rect.x + delta)
        self.apply_constraints()
        return self

    def set_y(self, y: float) -> Self:
        if y == self.rect.y : return self
        delta = y - self.rect.y
        self.rect.y = y
        for child in self.children:
            child.set_y(child.rect.y + delta)
        self.apply_constraints()
        return self

    def set_position(self, x: float, y: float) -> Self:
        if self.rect.topleft == (x,y) : return self
        delta_x = x - self.rect.x
        delta_y = y - self.rect.y
        self.rect.topleft = x, y
        for child in self.children:
            child.set_position(child.rect.x + delta_x, child.rect.y + delta_y)
        self.apply_constraints()
        return self

    def set_center(self, x: float, y: float) -> Self:
        if self.rect.center == (x,y) : return self
        delta_x = x - self.rect.centerx
        delta_y = y - self.rect.centery
        self.rect.center = x, y
        for child in self.children:
            child.set_position(child.rect.x + delta_x, child.rect.y + delta_y)
        self.apply_constraints()
        return self

    def set_size(self, size : tuple[float|None,float|None]) -> Self:
        width,height = size
        if width is None : width = self.rect.w
        if height is None : height = self.rect.h
        if self.rect.size == (width,height) : return self
        self.rect.size = (width, height)
        self.build()
        self.apply_constraints()
        self.notify()
        return self

    # Other Methods

    def print_tree(self, ident: int = 0) -> None:
        print("\t" * ident + self.to_string() + (":" if self.children else ""))
        for child in self.children:
            child.print_tree(ident + 1)

    def to_string(self) -> str:
        return f"{self.to_string_id()}@{*self.rect.topleft,* self.rect.size}"

    def to_string_id(self) -> str:
        return "Widget"

    def do_when_removed(self) -> None:
        if self.parent_scene and self.parent == self.parent_scene.root:
            self.set_parent(None)

    # Methods on children

    def add_child(self, *child: "Widget") -> Self:
        for c in child:
            self.children.append(c)
            c.set_parent(self)
            c.set_parent_scene(self.parent_scene)
            c.do_when_added()
        self._sort_children()
        self.apply_all_constraints()
        self.notify()
        return self

    def remove_child(self, child: "Widget") -> Self:
        try : 
            self.children.remove(child)
        except ValueError:
            return
        child.set_parent(None)
        child.do_when_removed()
        child.set_parent_scene(None)
        self._sort_children()
        self.apply_all_constraints()
        self.notify()
        return self

    def clear(self)->Self:
        self.children.clear()
        return self


    def _sort_children(self):
        self.children.sort(key=lambda child : child.render_order)


    # if return True -> don't propagate to siblings or parents
    def process_event(self, event: pygame.Event) -> bool:
        # First propagate to children
        for child in self.children:
            if child.process_event(event):
                return True
        # return True if the method is blocking (no propagation to next children of the scene)
        return super().process_event(event)

    def update(self, dt: float):
        for child in self.children:
            child.update(dt)
        self.do_update(dt)

    def _get_clipped_rect_and_area(self,camera: bf.Camera)->tuple[pygame.FRect,pygame.FRect]:
        transposed_rect = camera.world_to_screen(self.rect)
        # transposed_rect = self.rect.copy()
        # transposed_rect.topleft -= camera.rect.topleft
        parent_rect = self.parent.get_padded_rect()
        if isinstance(self.parent,bf.Container):
            parent_rect.move_ip(self.parent.scroll)
        clipped_rect = transposed_rect.clip(camera.world_to_screen(parent_rect))
        # We only need to adjust the source rectangle to match the portion within the clipped_rect.
        source_area = clipped_rect.move(-transposed_rect.x, -transposed_rect.y)
        return clipped_rect,source_area



    def draw(self, camera: bf.Camera) -> int:
        if not self.visible  or not camera.rect.colliderect(self.rect):
            return sum((child.draw(camera) for child in self.rect.collideobjectsall(self.children))) 
        
        if self.parent and self.clip_to_parent:
            clipped_rect,source_area = self._get_clipped_rect_and_area(camera)
            if clipped_rect.size == (0,0):
                return 0 
            else:
                camera.surface.blit(
                    self.surface,
                    clipped_rect.topleft,
                    source_area,
                    special_flags=self.blit_flags
                )
        else:
            camera.surface.blit(
                self.surface, camera.world_to_screen(self.rect),  
                special_flags = self.blit_flags
            )
        return 1 + sum((child.draw(camera) for child in self.rect.collideobjectsall(self.children)))

    def build(self) -> None:
        """
        This function is called each time the widget's surface has to be updated
        It usually has to be overriden if inherited to suit the needs of the new class
        """
        if self.surface.get_size() != self.get_size_int():
            self.surface = pygame.Surface(self.get_size_int())
        self.surface.set_alpha(self.alpha)

    def build_all(self) -> None:
        self.build()
        for child in self.children:
            child.build_all()

    def notify(self) -> None:
        if self.parent and not self.is_root:
            self.parent.notify()


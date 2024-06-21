from typing import TYPE_CHECKING,Self,Callable
from collections.abc import Iterable
import batFramework as bf
import pygame
if TYPE_CHECKING :
    from .constraints.constraints import Constraint
    from .root import Root
MAX_CONSTRAINTS = 10
class Widget(bf.Entity):
    def __init__(self,*args,**kwargs) -> None:
        super().__init__(*args,**kwargs)
        self.children: list["Widget"] = []
        self.constraints : list[Constraint] = []
        self.parent : "Widget" = None
        self.do_sort_children =False
        self.clip_children : bool = True
        self.padding = (0,  0,  0,  0)
        self.dirty_surface : bool = True #  if true will call paint before drawing 
        self.dirty_shape : bool = True #    if true will call (build+paint) before drawing
        self.dirty_constraints : bool = False
        self.is_root : bool = False
        self.autoresize_w,self.autoresize_h  = True,True
        self.__constraint_iteration = 0

    def set_clip_children(self,value:bool)->Self:
        self.clip_children = value
        self.dirty_surface = True
        return self

    def __str__(self)->str:
        return "Widget"

    def set_autoresize(self,value:bool)->Self:
        self.autoresize_w = self.autoresize_h = value
        self.dirty_shape = True
        return self

    def set_autoresize_w(self,value:bool)->Self:
        self.autoresize_w = value
        self.dirty_shape = True
        return self

    def set_autoresize_h(self,value:bool)->Self:
        self.autoresize_h = value
        self.dirty_shape = True
        return self

    def set_render_order(self,render_order:int)->Self:
        super().set_render_order(render_order)
        if self.parent:self.parent.do_sort_children = True
        return self


    def inflate_rect_by_padding(self,rect: pygame.Rect|pygame.FRect)->pygame.Rect|pygame.FRect:
        return pygame.FRect(
            rect[0] - self.padding[0],
            rect[1] - self.padding[1],
            rect[2] + self.padding[0] + self.padding[2],
            rect[3] + self.padding[1] + self.padding[3] 
        )
            
    def set_position(self, x, y) -> Self:
        if x is None: x = self.rect.x
        if y is None: y = self.rect.y
        if (x,y) == self.rect.topleft : return self
        dx,dy = x-self.rect.x,y-self.rect.y
        self.rect.topleft = x,y
        _ = [c.set_position(c.rect.x+dx,c.rect.y+dy) for c in self.children]
        return self

    def set_center(self,x,y)->Self:
        if x is None : x = self.rect.centerx
        if y is None : y = self.rect.centery
        if (x,y) == self.rect.center : return self
        dx,dy = x-self.rect.centerx,y-self.rect.centery
        self.rect.center = x,y
        _ = [c.set_center(c.rect.centerx+dx,c.rect.centery+dy) for c in self.children]
        return self     

    def set_parent_scene(self,parent_scene:bf.Scene)->Self:
        super().set_parent_scene(parent_scene)
        for c in self.children : 
            c.set_parent_scene(parent_scene) 
        return self
    
    def set_parent(self,parent:"Widget")->Self:
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

    def get_padded_rect(self)->pygame.FRect:
        r = self.rect.inflate(-self.padding[0]-self.padding[2],-self.padding[1]-self.padding[3])
        # r.normalize()
        return r

    def get_min_required_size(self)->tuple[float,float]:
        return self.rect.size

    def get_padded_width(self)->float:
        return self.rect.w - self.padding[0] - self.padding[2]
    
    def get_padded_height(self)->float:
        return self.rect.h - self.padding[1] - self.padding[3]
    
    def get_padded_left(self)->float:
        return self.rect.left + self.padding[0]

    def get_padded_right(self)->float:
        return self.rect.right + self.padding[2]

    def get_padded_center(self)->tuple[float,float]:
        return self.get_padded_rect().center

    def get_padded_top(self)->float:
        return self.rect.y + self.padding[1]

    def get_padded_bottom(self)->float:
        return self.rect.bottom - self.padding[3] 

    def get_debug_outlines(self):
        yield (self.rect, self.debug_color)
        if any(self.padding) : yield (self.get_padded_rect(),"gray")
        for child in self.children:
            yield from child.get_debug_outlines()

    def add_constraints(self,*constraints:"Constraint")->Self:
        self.constraints.extend(constraints)
        seen = set()
        result = []
        for c in self.constraints:
            if c.name not in seen:
                result.append(c)
                seen.add(c.name)
        self.constraints = result
        self.constraints.sort(key=lambda c : c.priority)
        self.dirty_constraints = True
        return self

    def resolve_constraints(self)->None:
        if self.parent is None or not self.constraints:
            self.dirty_constraints = False
            return
        all_good = False
        constraint_iteration = 0
        while not all_good:
            for constraint in self.constraints:
                if not constraint.evaluate(self.parent,self):
                    constraint.apply(self.parent,self)
                    # print(constraint.name,"Applied")
            constraint_iteration += 1
            if  all(c.evaluate(self.parent,self) for c in self.constraints):
               all_good = True
               break
            elif self.__constraint_iteration > MAX_CONSTRAINTS:
                print(self,"CONSTRAINTS ERROR",list(c.name for c in self.constraints if not c.evaluate(self.parent,self)))
                self.dirty_constraints = False
                return
        # print("DONE")
        self.dirty_constraints = False

    def remove_constraints(self,*names:str)->Self:
        self.constraints = [c for c in self.constraints if c.name not in names]
        return self

    def has_constraint(self,name:str)->bool:
        return any(c.name == name for c in self.constraints )

    def visit(self,func:Callable,top_down:bool = True)->None:
        if top_down : func(self)
        for child in self.children:
            child.visit(func,top_down)
        if not top_down: func(self)

    def get_root(self)->"Root":
        if self.is_root:
            return self
        return self.parent.get_root()

    def top_at(self, x: float | int, y: float | int) -> "None|Widget":
        if self.children:
            for child in reversed(self.children):
                if child.visible: 
                    r = child.top_at(x, y)
                    if r is not None:
                        return r
        return self if self.visible and self.rect.collidepoint(x, y) else None

    def add(self,*children:"Widget")->Self:
        self.children.extend(children)
        i = len(self.children)
        for child in children:
            child.set_render_order(i).set_parent(self).set_parent_scene(self.parent_scene)
            i += 1
        if self.parent:
            self.parent.do_sort_children = True
        return self

    def remove(self,*children:"Widget")->Self:
        for child in self.children[:]:
            if child in children:
                child.set_parent(None).set_parent_scene(None)
                self.children.remove(child)
        if self.parent:
            self.parent.do_sort_children = True

    def set_size_if_autoresize(self,size:tuple[float,float])->Self:
        size = list(size)
        size[0] = size[0] if self.autoresize_w else None
        size[1] = size[1] if self.autoresize_h else None

        self.set_size(size)

        return self

    def set_size(self,size:tuple)->Self:
        size = list(size)
        if size[0] is None : size[0] = self.rect.w
        if size[1] is None : size[1] = self.rect.h
        if size == self.rect.size : return self
        self.rect.size = size
        self.dirty_shape = True
        return self
    

    def process_event(self, event: pygame.Event) -> bool:
        # First propagate to children
        for child in self.children:
            child.process_event(event)
        # return True if the method is blocking (no propagation to next children of the scene)
        super().process_event(event)


    def update(self,dt)->None:
        if self.do_sort_children:
            self.children.sort(key = lambda c : c.render_order)
            self.do_sort_children = False
        _ = [c.update(dt) for c in self.children]
        super().update(dt)


    def build(self)->None:
        new_size =tuple(map(int,self.rect.size))       
        if self.surface.get_size() != new_size:
            new_size = [max(0,i) for i in new_size]
            self.surface = pygame.Surface(new_size,self.surface_flags)
            if self.convert_alpha : self.surface = self.surface.convert_alpha()

    def paint(self)->None:
        self.surface.fill((0,0,0,0))
        return self

    def visit_up(self,func)->None:
        if func(self) : return
        if self.parent:
            self.parent.visit_up(func)

    def selective_up(self,widget:"Widget"):
        # if returns True then stop climbing widget tree
        if widget.parent and widget.parent.dirty_constraints:
            return False
        widget.visit(self.selective_down)
        return True

    def selective_down(self,widget: "Widget"):
        if widget.constraints :
            widget.resolve_constraints()
        else:
            widget.dirty_constraints = False
        if widget.dirty_shape:
            widget.build()
            widget.dirty_shape = False
            self.dirty_surface = True


    def draw(self, camera: bf.Camera) -> None:
        if self.dirty_shape:
            self.dirty_constraints = True
            self.dirty_surface = True
            self.build()
            self.dirty_shape = False
            for child in self.children :
                child.dirty_constraints = True

        if self.dirty_constraints:
            if self.parent and self.parent.dirty_constraints:
                self.parent.visit_up(self.selective_up)
            else:
                self.visit(lambda c : c.resolve_constraints())

        if self.dirty_surface : 
            self.paint()
            self.dirty_surface = False



        super().draw(camera)
        if self.clip_children:

            new_clip = camera.world_to_screen(self.get_padded_rect())
            old_clip = camera.surface.get_clip()
            new_clip = new_clip.clip(old_clip)
            camera.surface.set_clip(new_clip)

        _ = [child.draw(camera) for child in sorted(self.children, key=lambda c: c.render_order)]
        if self.clip_children:
            camera.surface.set_clip(old_clip)
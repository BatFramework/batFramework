from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .constraints import Constraint
    from .root import Root
from typing import Self

import batFramework as bf
import pygame
from math import ceil



class Widget(bf.Entity):
    def __init__(self,convert_alpha=True)->None:
        super().__init__(convert_alpha=convert_alpha)
        self.autoresize = False
        self.parent : None|Self = None 
        self.is_root :bool = False
        self.children : list["Widget"] = []
        self.focusable :bool= False
        self.constraints : list[Constraint] = []
        self.gui_depth : int = 0
        if self.surface : self.surface.fill("white")
        self.set_debug_color("red")
        self.padding :tuple[float|int,...]= (0,0,0,0) 

    def set_padding(self,value : float|int|tuple|list)->Self:
        old_raw_size = (
            self.rect.w - self.padding[0] - self.padding[2],
            self.rect.h - self.padding[1] - self.padding[3]
        )
        if isinstance(value,list) or isinstance(value,tuple):
            if len(value) > 4 : pass
            elif any(v<0 for v in value) : pass
            elif len(value) == 2:
                self.padding = (value[0],value[1],value[0],value[1])
            else:
                self.padding = (*value, *self.padding[len(value):])
        else:
            self.padding = (value,)*4

        self.set_size(
            old_raw_size[0] + self.padding[0] +  self.padding[2],
            old_raw_size[1] + self.padding[1] +  self.padding[3],
        )
        if self.parent :
            self.apply_constraints()
            self.parent.children_modified()
        return self
        
    def inflate_rect_by_padding(self,rect:pygame.FRect)->pygame.FRect:
        return pygame.FRect(
            rect[0] - self.padding[0],
            rect[1]  - self.padding[1],
            rect[2] + self.padding[0]+self.padding[2],
            rect[3] + self.padding[1]+self.padding[3]   
        )
    def get_content_left(self)->float:
        return self.rect.left + self.padding[0]

    def get_content_top(self)->float:
        return self.rect.top + self.padding[1]

    def get_content_right(self)->float:
        return self.rect.right - self.padding[2]

    def get_content_bottom(self)->float:
        return self.rect.bottom - self.padding[3]

    def get_content_width(self)->float:
        return self.rect.w - self.padding[0] - self.padding[2]

    def get_content_height(self)->float:
        return self.rect.h - self.padding[1] - self.padding[3]

    def get_content_rect(self)->pygame.FRect:
        return pygame.FRect(
            self.rect.left      + self.padding[0],
            self.rect.top       + self.padding[1],
            self.get_content_width(),
            self.get_content_height()
        )

    def get_content_rect_rel(self)->pygame.FRect:
        return self.get_content_rect().move(-self.rect.left,-self.rect.top)

    def get_content_center(self)->tuple[float,float]:
        return self.get_content_rect().center

    def get_depth(self)->int:
        if self.is_root or self.parent is None : 
            self.gui_depth = 0
        else:
            self.gui_depth =  self.parent.get_depth() + 1
        return self.gui_depth

    def top_at(self, x: float, y: float) -> "None|Widget":
        if self.children:
            for child in reversed(self.children):
                r = child.top_at(x,y)
                if r is not None:
                    return r
        if self.rect.collidepoint(x,y) and self.visible:
            return self
        return None
            
    def get_constraint(self,name:str)->Constraint|None:
        return next((c for c in self.constraints if c.name == name), None)

    def add_constraints(self,*constraints:Constraint)->Self:
        for constraint in constraints:
            c = self.get_constraint(constraint.name)
            if c is not None:
                self.constraints.remove(c)
            self.constraints.append(constraint)
        self.apply_constraints()
        return self


    def has_constraint(self,name:str)->bool:
        return any(c.name == name for c in self.constraints)

    def apply_all_constraints(self)->None:
        # print("APPLY ALL CONSTRAINTS IN ",self.to_string())
        self.apply_constraints()
        for child in self.children : child.apply_all_constraints()
    
    def apply_constraints(self, max_iterations: int = 10) -> None:
        if not self.parent:
            # print(f"Warning : can't apply constraints on {self.to_string()} without parent widget")
            return
        if not self.constraints:
            return
        # Sort constraints based on priority
        self.constraints.sort(key=lambda c: c.priority)

        for iteration in range(max_iterations):
            unsatisfied = []  # Initialize a flag

            for constraint in self.constraints:
                if not constraint.evaluate(self.parent, self):
                    unsatisfied.append(constraint)
                    constraint.apply(self.parent, self)
            if not unsatisfied:
            #     data = ''.join(f"\n\t->{c.to_string()}" for c in self.constraints)
            #     print(self.get_depth()*'\t'+f"Following constraints of {self.to_string()} were all satisfied :{data}")
                break
            # print(f"pass {iteration}/{max_iterations} : unsatisfied = {';'.join(c.to_string() for c in unsatisfied)}")
            if iteration == max_iterations - 1:
                raise ValueError(f"[WARNING] Following constraints for {self.to_string()} were not satisfied : \n\t{';'.join([c.to_string() for c in unsatisfied])}")

    # GETTERS
    def get_by_tags(self,*tags):
        for c in self.children:
            yield from c.get_by_tags(*tags)
        if any(self.has_tag(t) for t in tags):
            yield self

    def get_root(self)-> Self|Root|None:
        if self.is_root: return self
        if self.parent_scene is not None : return self.parent_scene.root
        return None if self.parent is None else self.parent.get_root()

    def get_size_int(self)->tuple[int,int]:
        return (ceil(self.rect.width),ceil(self.rect.height))


    def get_center(self)->tuple[float,float]:
        return self.rect.center


    def get_bounding_box(self):
        yield (self.rect,self._debug_color)
        yield (self.get_content_rect(),"yellow")
        for child in self.children:
            yield from child.get_bounding_box()

    def set_autoresize(self,value:bool)-> Self:
        self.autoresize = value
        self.build()
        return self

    def set_parent(self,parent:Self|None)->None:
        if self.parent:
            self.parent.remove_child(self)
        self.parent = parent
        self.apply_all_constraints()
    # SETTERS
    
    def set_root(self) -> Self:
        self.is_root = True
        return self

    def set_parent_scene(self,scene)->None:
        super().set_parent_scene(scene)
        for child in self.children : 
            child.set_parent_scene(scene)

    def set_x(self,x:float)->Self:
        delta = x - self.rect.x
        self.rect.x = x
        for child in self.children:
            child.set_x(child.rect.x + delta)
        self.apply_constraints()
        return self

    def set_y(self,y:float)->Self:
        delta = y - self.rect.y
        self.rect.y = y
        for child in self.children:
            child.set_y(child.rect.y + delta)
        self.apply_constraints()

        return self

    def set_position(self,x:float,y:float)->Self:
        delta_x = x - self.rect.x
        delta_y = y - self.rect.y
        self.rect.topleft = x,y
        for child in self.children:
            child.set_position(child.rect.x + delta_x,child.rect.y+delta_y)
        self.apply_constraints()
        return self
        
    def set_center(self,x:float,y:float)->Self:
        delta_x = x - self.rect.centerx
        delta_y = y - self.rect.centery
        self.rect.center = x,y
        for child in self.children:
            child.set_position(child.rect.x + delta_x,child.rect.y+delta_y)
        self.apply_constraints()
        return self


    def set_size(self, width : float, height: float) -> Self:
        self.rect.size = (width,height)
        self.build()

        return self
        

    # Other Methods

    def print_tree(self,ident:int=0)->None:
        print('\t'*ident+self.to_string()+(':' if self.children else ''))
        for child in self.children :
            child.print_tree(ident+1)

    def to_string(self)->str:
        
        return f"{self.to_string_id()}@{*self.rect.topleft,* self.rect.size}"


    def to_string_id(self)->str:
        return "Widget"


    def do_when_removed(self)->None:
        if self.parent_scene and self.parent == self.parent_scene.root:
            self.set_parent(None)

    # Methods on children

    def add_child(self,*child:"Widget")->None:
        for c in child : 
            self.children.append(c)
            c.set_parent(self)
            c.set_parent_scene(self.parent_scene)
            c.apply_constraints()
        self.apply_constraints()
        self.children_modified()

    def remove_child(self,child:Self)->None:
        self.children.remove(child)
        child.set_parent(None)
        child.set_parent_scene(None)
        self.apply_constraints()
        self.children_modified()




    # if return True -> don't propagate to siblings or parents
    def process_event(self, event: pygame.Event)->bool:
    
        # First propagate to children
        for child in self.children:
            if child.process_event(event):
                return True
         #return True if the method is blocking (no propagation to next children of the scene)
        return super().process_event(event)


    def update(self,dt:float):
        for child in self.children:
            child.update(dt)

    def draw(self, camera: bf.Camera) -> int:
        self.children.sort(key=lambda e: (e.z_depth,e.render_order))
        return super().draw(camera) + sum([child.draw(camera) for child in self.children])

    def build(self)->None:
        """
        This function is called each time the widget's surface has to be updated
        It usually has to be overriden if inherited to suit the needs of the new class
        """
        if not self.surface: return
        if self.surface.get_size() != self.get_size_int():
            self.surface = pygame.Surface(self.get_size_int())
            self.apply_constraints()
            if self.parent : 
                self.parent.children_modified()

    def build_all(self)->None:
        for child in self.children:
            child.build_all()
        self.build()
    def children_modified(self)->None:
        if self.parent and not self.is_root:
            self.parent.children_modified()

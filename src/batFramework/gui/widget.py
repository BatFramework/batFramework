import batFramework as bf
import pygame
from math import ceil
from .constraints import Constraint
from typing import Self

class Widget(bf.Entity):
    def __init__(self,convert_alpha=True)->None:
        super().__init__(convert_alpha=convert_alpha)
        self.autoresize = False
        self.parent : None|Self = None 
        self.is_root :bool = False
        self.children : list[Self] = []
        self.focusable :bool= False
        self.constraints : list[Constraint] = []
        self.gui_depth : int = 0
        if self.surface : self.surface.fill("white")
        self.set_debug_color("green")

    def get_depth(self)->int:
        if self.is_root or self.parent is None : 
            self.gui_depth = 0
        else:
            self.gui_depth =  self.parent.get_depth() + 1
        return self.gui_depth

    def top_at(self, x: float, y: float) -> None|Self:
        if self.children:
            for child in reversed(self.children):
                r = child.top_at(x,y)
                if r is not None:
                    return r
        if self.rect.collidepoint(x,y) and self.visible:
            return self
        return None
            
    def get_constraint(self,name:str)->Constraint:
        return next((c for c in self.constraints if c.name == name), None)

    def add_constraints(self,*constraints:Constraint)->Self:
        for c in constraints:
            self.add_constraint(c)
        return self
    def add_constraint(self,constraint:Constraint)->Self:
        c = self.get_constraint(constraint.name)
        if c is not None:
            self.constraints.remove(c)
        self.constraints.append(constraint)
        self.apply_constraints()
        return self

    def has_constraint(self,name:str)->str:
        return any(c.name == name for c in self.constraints)

    def apply_all_constraints(self)->None:
        self.apply_constraints()
        for child in self.children : child.apply_constraints()

    
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
                # data = ''.join(f"\n\t->{c.to_string()}" for c in self.constraints)
                # print(f"Following constraints of {self.to_string()} were all satisfied :{data}")
                break
            # print(f"pass {iteration}/{max_iterations} : unsatisfied = {';'.join(c.to_string() for c in unsatisfied)}")
            if iteration == max_iterations - 1:
                raise ValueError(f"Following constraints for {self.to_string()} were not satisfied : \n\t{';'.join([c.to_string() for c in unsatisfied])}")


    # GETTERS
    def get_root(self)-> Self:
        if self.is_root: return self
        if self.parent_scene is not None : return self.parent_scene.root
        return None if self.parent is None else self.parent.get_root()


    def get_size_int(self)->tuple[int,int]:
        return (ceil(self.rect.width),ceil(self.rect.height))


    def get_center(self)->tuple[float,float]:
        return self.rect.center


    def get_bounding_box(self):
        yield self.rect
        for child in self.children:
            yield from child.get_bounding_box()

    def set_autoresize(self,value:bool)-> Self:
        self.autoresize = value
        return self

    def set_parent(self,parent:Self)->None:
        self.parent = parent
        self.apply_constraints()
        
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
        return self

    def set_y(self,y:float)->Self:
        delta = y - self.rect.y
        self.rect.y = y
        for child in self.children:
            child.set_y(child.rect.y + delta)
        return self

    def set_position(self,x:float,y:float)->Self:
        delta_x = x - self.rect.x
        delta_y = y - self.rect.y
        self.rect.topleft = x,y
        for child in self.children:
            child.set_position(child.rect.x + delta_x,child.rect.y+delta_y)
        return self
        
    def set_center(self,x:float,y:float)->Self:
        delta_x = x - self.rect.centerx
        delta_y = y - self.rect.centery
        self.rect.center = x,y
        for child in self.children:
            child.set_position(child.rect.x + delta_x,child.rect.y+delta_y)
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

    def do_when_added(self)->None:
        if self.parent is None:
            self.set_parent(self.parent_scene.root)

    def do_when_removed(self)->None:
        if self.parent == self.parent_scene.root:
            self.set_parent(None)


    # Methods on children

    def add_child(self,*child:Self)->None:
        for c in child : 
            self.children.append(c)
            c.set_parent(self)
            c.set_parent_scene(self.parent_scene)

    def remove_child(self,child:Self)->None:
        self.children.remove(child)
        child.set_parent(None)
        child.set_parent_scene(None)



    # if return True -> don't propagate to siblings or parents
    def process_event(self, event: pygame.Event)->bool:

        # First propagate to children
        for child in self.children:
            # if event.type == pygame.MOUSEBUTTONDOWN :print("Propagate in :",self.to_string())
            if child.process_event(event):
                # if event.type == pygame.MOUSEBUTTONDOWN : print("\t",child.to_string(),"BLOCK ! ABORT !!!")
                return True
            # if event.type == pygame.MOUSEBUTTONDOWN : print("\t",child.to_string(),"pass")
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
        if self.parent : self.parent.children_modified()

    def children_modified(self)->None:
        self.apply_constraints()
        if self.parent and not self.is_root:
            self.parent.children_modified()

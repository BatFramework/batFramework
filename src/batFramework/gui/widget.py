import batFramework as bf
import pygame
from math import ceil
from .constraints import Constraint

class Widget(bf.Entity):
    def __init__(self)->None:
        super().__init__(convert_alpha=True)
        # Resize the widget size according to the text
        self.autoresize = True
        self.parent : None|"Widget" = None 
        self.is_root :bool = False
        self.children : list["Widget"] = []
        self.focusable :bool= False
        self.is_focused :bool= False
        self.constraints : list[Constraint] = []
        
        if self.surface : self.surface.fill("white")
        self.set_debug_color("green")

    def add_constraint(self,constraint:Constraint)->"Widget":
        self.constraints.append(constraint)
        self.apply_constraints()
        return self

    def has_constraint(self,name:str)->str:
        return any(c.name == name for c in self.constraints)

    def apply_all_constraints(self)->None:
        self.apply_constraints()
        for child in self.children : child.apply_constraints()

    
    def apply_constraints(self, max_iterations: int = 10) -> None:
        if not self.constraints or not self.parent:
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
                print(f"pass {iteration}/{max_iterations} : unsatisfied = {unsatisfied}")
                break
                
            if iteration == max_iterations - 1:
                raise ValueError(f"Following constraints for {self.to_string()} were not satisfied : \n\t{','.join([c.name for c in unsatisfied])}")
        
    def get_root(self)-> "Widget":
        if self.is_root: return self
        if self.parent_scene is not None : return self.parent_scene.root
        return None if self.parent is None else self.parent.get_root()

    def set_autoresize(self,value:bool)-> "Label":
        self.autoresize = value
        return self

    def set_parent(self,parent:"Widget")->None:
        self.parent = parent
        self.apply_constraints()
        
    def get_focus(self)->bool:
        if self.parent is None or not self.focusable: return False
        self.get_root().focus_on(self)
        if not self.parent.is_focused:
            self.parent.get_focus()
        self.focused = True
        

    def get_bounding_box(self):
        yield self.rect
        for child in self.children:
            yield from child.get_bounding_box()

    def set_x(self,x:float)->"Widget":
        delta = x - self.rect.x
        self.rect.x = x
        for child in self.children:
            child.set_x(child.rect.x + delta)
        return self

    def set_y(self,y:float)->"Widget":
        delta = y - self.rect.y
        self.rect.y = y
        for child in self.children:
            child.set_y(child.rect.y + delta)
        return self

    def set_position(self,x:float,y:float)->"Widget":
        delta_x = x - self.rect.x
        delta_y = y - self.rect.y
        self.rect.topleft = x,y
        for child in self.children:
            child.set_position(child.rect.x + delta_x,child.rect.y+delta_y)
        return self
        
    def set_center(self,x:float,y:float)->"Widget":
        delta_x = x - self.rect.centerx
        delta_y = y - self.rect.centery
        self.rect.center = x,y
        for child in self.children:
            child.set_position(child.rect.x + delta_x,child.rect.y+delta_y)
        return self

    def get_center(self)->tuple[float,float]:
        return self.rect.center


    def print_tree(self,ident:int=0)->None:
        print('\t'*ident+self.to_string()+(':' if self.children else ''))
        for child in self.children :
            child.print_tree(ident+1)

    def to_string(self)->str:
        
        return f"Widget@{*self.rect.topleft,* self.rect.size}"

    def set_root(self) -> "Widget":
        self.is_root = True
        return self

    def add_child(self,*child:"Widget")->None:
        for c in child : 
            self.children.append(c)
            c.set_parent(self)

    def remove_child(self,child:"Widget")->None:
        self.children.remove(child)
        child.set_parent(None)

    # if return True -> don't propagate upwards
    def process_event(self, event: pygame.Event)->bool:
        # insert action process here
        for child in self.children:
            if child.process_event(event):
                return False
        self.do_handle_event(event)
        # insert action reset heres

         #return True if the method is blocking (no propagation to next children of the scene)
        return False

    def update(self,dt:float):
        for child in self.children:
            child.update(dt)

    def draw(self, camera: bf.Camera) -> int:
        return super().draw(camera) +\
         sum([child.draw(camera) for child in self.children])

    def set_size(self, width : float, height: float) -> "Widget":
        self.rect.size = (width,height)
        self.build()
        return self
        
    def get_size_int(self)->tuple[int,int]:
        return (ceil(self.rect.width),ceil(self.rect.height))

    def build(self)->None:
        """
        This function is called each time the widget's surface has to be updated
        It usually has to be overriden if inherited to suit the needs of the new class
        """
        if not self.surface: return
        if self.surface.get_size() != self.get_size_int():
            self.surface = pygame.Surface(self.get_size_int())
    

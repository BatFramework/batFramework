import batFramework as bf
import pygame
from math import ceil

class GUIEntity(bf.Entity):
    def __init__(self)->None:
        super().__init__(convert_alpha=True)
        self.parent : None|"GUIEntity" = None 
        self.is_root :bool = False
        self.children : list["GUIEntity"] = []
        self.set_debug_color("green")
        if self.surface : self.surface.fill("white")

    def print_tree(self,ident:int=0)->None:
        print('\t'*ident+self.to_string()+(':' if self.children else ''))
        for child in self.children :
            child.print_tree(ident+1)

    def to_string(self)->str:
        if self.is_root : 
            return "ROOT"
        else :
            return f"GUIEntity@{self.rect.topleft}|{self.rect.size}"

    def set_root(self) -> "GUIEntity":
        self.is_root = True
        return self

    def add_child(self,child:"GUIEntity")->None:
        self.children.append(child)

    # if return True -> don't propagate upwards
    def process_event(self, event: pygame.Event)->bool:
        # insert action process here
        for child in self.children:
            if child.process_event(event):
                return False
        self.do_handle_event(event)
        # insert action reset heres
        return True

    def update(self,dt:float):
        for child in self.children:
            child.update(dt)

    def draw(self, camera: bf.Camera) -> int:
        return super().draw(camera) +\
         sum([child.draw(camera) for child in self.children])

    def set_size(self, width : float, height: float) -> "GUIEntity":
        self.rect.size = (width,height)
        return self
    def get_size_int(self)->tuple[int,int]:
        return (ceil(i) for i in self.rect.size)

    def build(self)->None:
        if not self.surface: return
        if self.surface.get_size() != self.get_size_int():
            self.surface = pygame.Surface(self.get_size_int())
    

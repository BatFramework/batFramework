import batFramework as bf
import pygame
from math import ceil

class Widget(bf.Entity):
    def __init__(self)->None:
        super().__init__(convert_alpha=True)
        self.parent : None|"Widget" = None 
        self.is_root :bool = False
        self.children : list["Widget"] = []
        self.set_debug_color("green")
        if self.surface : self.surface.fill("white")

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
        if self.is_root : 
            return "ROOT"
        else :
            return f"Widget@{*self.rect.topleft,* self.rect.size}"

    def set_root(self) -> "Widget":
        self.is_root = True
        return self

    def add_child(self,child:"Widget")->None:
        self.children.append(child)

    def remove_child(self,child:"Widget")->None:
        self.children.remove(child)


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

    def set_size(self, width : float, height: float) -> "Widget":
        self.rect.size = (width,height)
        self.build()
        return self
        
    def get_size_int(self)->tuple[int,int]:
        return (ceil(self.rect.width),ceil(self.rect.height))

    def build(self)->None:
        if not self.surface: return
        if self.surface.get_size() != self.get_size_int():
            self.surface = pygame.Surface(self.get_size_int())
    

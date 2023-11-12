import batFramework as bf
from .interactiveWidget import InteractiveWidget
from .widget import Widget
import pygame

class Root(InteractiveWidget):
    def __init__(self):
        super().__init__()
        self.surface = None
        self.set_root()
        self.rect.size = pygame.display.get_surface().get_size()
        self.focused : InteractiveWidget = self
        self.hovered : Widget|None = self
        self.set_debug_color("purple")

    def to_string(self)->str:
         return "ROOT"

    def get_focused(self)->Widget|None:
        return self.focused

    def get_hovered(self)->Widget|None:
        return self.hovered
         
    def to_string_id(self)->str:
        return "ROOT"

    def focus_on(self,widget:InteractiveWidget)->None:
        if self.focused is not None: 
            self.focused.on_lose_focus()
        if widget is None :
            self.focused = self
            return
        self.focused= widget
        self.focused.on_get_focus()

    def set_size(self,width:float,height:float,force:bool=False)->"Root":
        if not force :  return self
        self.rect.size = width,height
        self.build(apply_constraints=True)
        return self
        
    def build(self,apply_constraints:bool=False)->None:
        if apply_constraints : self.apply_all_constraints()
        for child in self.children : 
            child.build()
    
    def do_handle_event(self,event):
        if event.type == pygame.VIDEORESIZE:
            self.set_size(event.w,event.h,force=True)
            return True
        return False

    def update(self,dt:float)->None:
        super().update(dt)
        self.hovered = self.top_at(*pygame.mouse.get_pos()) if self.top_at(*pygame.mouse.get_pos()) else None
        


        

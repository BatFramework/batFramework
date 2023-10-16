import batFramework as bf
from .widget import Widget
import pygame

class Root(Widget):
    def __init__(self):
        super().__init__()
        self.focusable = True
        self.surface = None
        self.set_root()
        self.rect.size = pygame.display.get_surface().get_size()
        self.focused_widget : Widget = self

    def to_string(self)->str:
         return "ROOT"

    def focus_on(self,widget:Widget)->None:
        self.focused_widget= widget

    def set_size(self,width:float,height:float,force:bool=False)->"Root":
        if not force :  return self
        self.rect.size = width,height
        self.build(apply_constraints=True)
        print("BUILD ALL")
        return self
    def build(self,apply_constraints:bool=False)->None:
        if apply_constraints : self.apply_all_constraints()
        for child in self.children : 
            child.build()
            
    def do_handle_event(self,event):
        if event.type == pygame.VIDEORESIZE:
            
            self.set_size(event.w,event.h,force=True)

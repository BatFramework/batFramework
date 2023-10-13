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


    def focus_on(self,widget:Widget)->None:
        self.focused_widget= widget

    def set_size(self,width:float,height:float)->"Root":
        return self

    def build(self)->None:
        pass

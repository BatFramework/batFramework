import batFramework as bf
from .widget import Widget
import pygame

class Root(Widget):
    def __init__(self):
        super().__init__()
        self.surface = None
        self.set_root()
        self.rect.size = pygame.display.get_surface().get_size()

    def set_size(self,width:float,height:float)->"Root":
        return self

    def build(self)->None:
        pass

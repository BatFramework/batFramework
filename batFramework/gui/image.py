import batFramework as bf
import pygame

class Image(bf.Entity):
    def __init__(self, path=None,convert_alpha = True) -> None:
        super().__init__(None)
        
        if path : self.set_image(path,convert_alpha=convert_alpha)
        self.set_debug_color(bf.color.GREEN)
        self.flipped = False

    def set_image(self,path,convert_alpha):
        self.surface = pygame.image.load(bf.utils.get_path(path))
        self.surface = self.surface.convert_alpha() if convert_alpha else self.surface.convert()
        self.rect.size = self.surface.get_size()
        
    def set_flip(self,value:bool):
        if value == self.flipped : return
        self.flipped = value
        self.surface = pygame.transform.flip(self.surface,value,False)
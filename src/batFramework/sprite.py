import batFramework as bf
import pygame
from typing import Self


class Sprite(bf.Entity):
    def __init__(
        self,
        path=None,
        size: None | tuple[int, int] = None,
        convert_alpha: bool = True,
    ):
        self.original_surface: pygame.Surface = None

        super().__init__(convert_alpha = convert_alpha)
        if path is not None:
            self.from_path(path)
        if size is not None and self.original_surface:
            self.set_size(self.original_surface.get_size())


    def set_size(self,size:tuple[float,float]) -> Self:
        if size == self.rect.size : return self
        self.rect.size = size
        self.surface = pygame.Surface((int(self.rect.w),int(self.rect.h)),self.surface_flags)
        if self.convert_alpha : self.surface = self.surface.convert_alpha()
        self.surface.fill((0,0,0,0 if self.convert_alpha else 255))
        self.surface.blit(pygame.transform.scale(self.original_surface,self.rect.size),(0,0))
        return self
            
    def from_path(self,path:str)->Self:
        tmp = bf.ResourceManager().get_image(path,self.convert_alpha)
        if tmp is None:
            return self
        self.original_surface = tmp
        size = self.original_surface.get_size()
        self.set_size(size)
        return self

    def from_surface(self,surface: pygame.Surface)->Self:
        if surface is None : return self
        self.original_surface = surface
        size = self.original_surface.get_size()
        self.set_size(size)
        return self
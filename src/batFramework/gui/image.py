import batFramework as bf
from .widget import Widget
import pygame
from typing import Self


class Image(Widget):
    def __init__(
        self,
        path: str = None,
        convert_alpha=True,
    ):
        self.original_surface = None
        super().__init__(convert_alpha = convert_alpha)
        if path is not None:
            self.from_path(path)

    def paint(self) -> None:
        super().paint()
        self.surface.fill((0,0,0,0 if self.convert_alpha else 255))
        if self.rect.size != self.original_surface.get_size():
            self.surface.blit(pygame.transform.scale(self.original_surface,self.rect.size),(0,0))
        else:
            self.surface.blit(self.original_surface,(0,0))
    def from_path(self,path:str)->Self:
        tmp = bf.ResourceManager().get_image(path,self.convert_alpha)
        if tmp is None:
            return Self
        self.original_surface = tmp
        if self.autoresize:
            self.set_size(self.original_surface.get_size())
        self.dirty_surface = True
        return self

    def from_surface(self,surface: pygame.Surface)->Self:
        if surface is None : return self
        self.original_surface = surface
        if self.autoresize:
            self.set_size(self.original_surface.get_size())
        self.dirty_surface = True
        return self
import batFramework as bf
import pygame
from typing import Self

class Sprite(bf.DynamicEntity):
    def __init__(
        self,
        data: pygame.Surface | str,
        size: None | tuple[int, int] = None,
        convert_alpha: bool = True,
    ):
        self.original_surface = None
        super().__init__(convert_alpha=convert_alpha)
        if data:
            self.set_image(data, size)
    
    def set_image(
        self, data: pygame.Surface | str, size: None | tuple[int, int] = None
    ):
        if isinstance(data, str):
            tmp = bf.ResourceManager().get_image(data,self.convert_alpha)
            self.original_surface = tmp
        elif isinstance(data, pygame.Surface):
            self.original_surface = data
        if self.convert_alpha:
            self.original_surface = self.original_surface.convert_alpha()
        if not size:
            size = self.original_surface.get_size()
        self.surface = pygame.transform.scale(self.original_surface, size)
        self.rect = self.surface.get_frect(center=self.rect.center)


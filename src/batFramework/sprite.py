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
    )->Self:
        if isinstance(data, str):
            tmp = bf.ResourceManager().get_image(data,self.convert_alpha)
            if tmp == None : print(f"Image file at '{data}' was not found :(")
            self.original_surface = tmp
        elif isinstance(data, pygame.Surface):
            self.original_surface = data
        else:
            raise ValueError("Image data can be either path or Surface")
        if self.convert_alpha:
            self.original_surface = self.original_surface.convert_alpha()
        if not size:
            size = self.original_surface.get_size()

        self.set_size(size)
        return self


    def set_size(self,size : tuple[int|None,int|None])->Self:
        new_size = []
        new_size[0] = size[0] if size[0] is not None else self.rect.w
        new_size[1] = size[1] if size[1] is not None else self.rect.h
        self.surface = pygame.transform.scale(self.original_surface, new_size)
        self.rect = self.surface.get_frect(center=self.rect.center)
        return self
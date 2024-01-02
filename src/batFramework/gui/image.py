import batFramework as bf
from .widget import Widget
import pygame


class Image(Widget):
    def __init__(
        self,
        data: pygame.Surface | str | None = None,
        size: None | tuple[int, int] = None,
        convert_alpha=True,
    ):
        self.dirty : bool = False
        self.original_surface = None
        self.surface = None
        super().__init__(convert_alpha)
        if data:
            self.set_image(data,size)

    def build(self) -> None:
        if self.original_surface and (
            (not self.surface or self.surface.get_size() != self.get_size_int()) 
            or self.dirty
        ) :
            self.surface = pygame.transform.scale(
                self.original_surface, self.get_size_int()
            )

    def set_image(
        self, data: pygame.Surface | str, size: None | tuple[int, int] = None
    ):
        if isinstance(data, str):
            path = bf.utils.get_path(data)
            tmp = pygame.image.load(path)
        elif isinstance(data, pygame.Surface):
            tmp= data
        if self.convert_alpha:
            tmp = tmp.convert_alpha()
        if tmp != self.original_surface: self.dirty = True
        self.original_surface = tmp
        if not size:
            size = self.original_surface.get_size()
        self.set_size(*size)

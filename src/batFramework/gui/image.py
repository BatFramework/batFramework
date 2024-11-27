import batFramework as bf
from .widget import Widget
from .shape import Shape
import pygame
from typing import Self


class Image(Shape):
    def __init__(
        self,
        path: str = None,
        convert_alpha=True,
    ):
        self.original_surface = None
        super().__init__(convert_alpha=convert_alpha)
        if path is not None:
            self.from_path(path)

    def __str__(self) -> str:
        return "Image"

    def paint(self) -> None:
        super().paint()
        if self.original_surface is None:
            return
        padded = self.get_padded_rect().move(-self.rect.x,-self.rect.y)
        target_size = padded.size
        if self.original_surface.get_size() != target_size:
            self.surface.blit(pygame.transform.scale(self.original_surface, target_size), padded.topleft)
        else:
            self.surface.blit(self.original_surface, padded.topleft)

    def build(self) -> None:
        if self.original_surface is not None:
            self.set_size_if_autoresize(
                self.inflate_rect_by_padding((0,0,*self.original_surface.get_size())).size
            )
        super().build()

    def get_min_required_size(self) -> tuple[float, float]:
        res = self.rect.size
        return self.inflate_rect_by_padding((0, 0, *res)).size




    def from_path(self, path: str) -> Self:
        tmp = bf.ResourceManager().get_image(path, self.convert_alpha)
        if tmp is None:
            return self
        self.original_surface = tmp
        size = self.original_surface.get_size()
        self.set_size(size)
        self.dirty_surface = True
        return self

    def from_surface(self, surface: pygame.Surface) -> Self:
        if surface is None:
            return self
        self.original_surface = surface
        size = self.original_surface.get_size()
        self.set_size(size)

        self.dirty_surface = True
        return self

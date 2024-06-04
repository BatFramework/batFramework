from typing import Any, Self
import pygame
import batFramework as bf
from .object import Object

class Entity(Object):
    """
    Basic entity class
    """
    def __init__(
        self,
        size: None | tuple[int, int] = None,
        surface_flags: int = 0,
        convert_alpha: bool = False,
        *args,
        **kwargs,
    ) -> None:
        super().__init__()
        self.visible: bool = True
        self.rect.size = (10, 10) if size is None else size
        self.convert_alpha: bool = convert_alpha
        self.surface_flags: int = surface_flags
        self.blit_flags: int = 0
        self.surface: pygame.Surface = pygame.Surface(self.rect.size, surface_flags)
        if convert_alpha:
            self.surface = self.surface.convert_alpha()
            self.surface.fill((0, 0, 0, 0))

    def set_alpha(self, alpha: int) -> Self:
        self.surface.set_alpha(min(max(0, alpha), 255))
        return self

    def get_alpha(self)->int:
        return self.surface.get_alpha()

    def set_surface_flags(self, surface_flags: int) -> Self:
        self.surface_flags = surface_flags
        return self

    def set_convert_alpha(self, value: bool) -> Self:
        self.convert_alpha = value
        return self

    def set_blit_flags(self, blit_flags: int) -> Self:
        self.blit_flags = blit_flags
        return self

    def set_render_order(self, render_order: int) -> Self:
        self.render_order = render_order
        if self.parent_scene:
            self.parent_scene.sort_entities()
        return self

    def set_visible(self, value: bool) -> Self:
        self.visible = value
        return self

    def draw(self, camera: bf.Camera) -> None:
        """
        Draw the entity onto the camera surface
        """
        if not self.visible or not camera.rect.colliderect(self.rect): return
        camera.surface.blit(
            self.surface,
            camera.world_to_screen(self.rect),
            special_flags=self.blit_flags,
        )

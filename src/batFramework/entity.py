from typing import Any, Self
import pygame
import batFramework as bf
from typing import TYPE_CHECKING
from .object import Object
if TYPE_CHECKING:
    from .camera import Camera
class Entity(Object):
    """
        Basic entity class
    """

    def __init__(
        self,
        size: None | tuple[int, int] = None,
        surface_flags: int = 0,
        convert_alpha: bool = False,
    ) -> None:
        super().__init__()
        if size is None:
                size = (10, 10)
        self.rect.size = size
        self.convert_alpha = convert_alpha
        self.blit_flags :int = 0# pygame.BLEND_PREMULTIPLIED if self.convert_alpha else 0
        
        self.surface  : pygame.Surface = pygame.Surface(size, surface_flags).convert()
        if convert_alpha:
            self.surface = self.surface.convert_alpha()
            self.surface.fill((0, 0, 0, 0))
    

    def set_alpha(self,alpha:int)->Self:
        self.surface.set_alpha(min(max(0,alpha),255))
        return self
        
    def set_blit_flags(self,blit_flags:int)->Self:
        self.blit_flags = blit_flags
        return self

    def set_render_order(self, render_order: int) -> Self:
        self.render_order = render_order
        if self.parent_scene: self.parent_scene.sort_entities()
        return self

    def set_visible(self, value: bool) -> Self:
        self.visible = value
        return self
    

    def draw(self, camera: bf.Camera) -> int:
        """
            Draw the entity onto the camera with coordinate transposing
        """
        if not self.visible or not camera.rect.colliderect(self.rect):
            return 0
        camera.surface.blit(
            self.surface,
            camera.world_to_screen(self.rect),
            special_flags = self.blit_flags)
        return 1

from typing import Any, Self
import pygame
import batFramework as bf
from .entity import Entity


class Drawable(Entity):
    """
    Basic entity class
    """

    def __init__(
        self,
        size: None | tuple[int|float] = None,
        surface_flags: int = 0,
        convert_alpha: bool = False,
        *args,
        **kwargs,
    ) -> None:
        super().__init__()
        self.visible: bool = True
        self.render_order: int = 0
        if size is not None:
            self.rect.size = size
        self.convert_alpha: bool = convert_alpha
        self.surface_flags: int = surface_flags
        self.blit_flags: int = 0
        self.drawn_by_group : bool = False # flag for render group  
        self.surface: pygame.Surface = pygame.Surface(self.rect.size, surface_flags)
        if convert_alpha:
            self.surface = self.surface.convert_alpha()
            self.surface.fill((0, 0, 0, 0))

    def set_alpha(self, alpha: int) -> Self:
        self.surface.set_alpha(min(max(0, alpha), 255))
        return self

    def get_alpha(self) -> int:
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

    def get_debug_outlines(self):
        if self.visible:
            yield (self.rect, self.debug_color)

    def set_render_order(self, render_order: int) -> Self:
        self.render_order = render_order
        if self.parent_layer:
            self.parent_layer.update_draw_order()
        return self

    def set_visible(self, value: bool) -> Self:
        self.visible = value
        return self

    def get_mask(self)->pygame.Mask:
        return pygame.mask.from_surface(self.surface)

    def mask_collide_point(self,point)->bool:
        if not self.rect.collidepoint(point):
            return False
        mask = pygame.mask.from_surface(self.surface)
        x = point[0]-  self.rect.x
        y = point[1] - self.rect.y
        return mask.get_at((x,y))==1




    def set_size(self, size: tuple[float, float]) -> Self:
        """
            Will erase surface data and create new empty surface
        """
        if size == self.rect.size:
            return self
        self.rect.size = size
        self.surface = pygame.Surface(
            (int(self.rect.w), int(self.rect.h)), self.surface_flags
        )
        if self.convert_alpha:
            self.surface = self.surface.convert_alpha()
        self.surface.fill((0, 0, 0, 0 if self.convert_alpha else 255))

        return self

    def draw(self, camera: bf.Camera) -> None:
        """
        Draw the entity onto the camera surface
        """
        if not self.visible or self.drawn_by_group or not camera.world_rect.colliderect(self.rect) or self.surface.get_alpha() == 0:
            return
        camera.surface.blit(
            self.surface,
            camera.world_to_screen(self.rect),
            special_flags=self.blit_flags,
        )

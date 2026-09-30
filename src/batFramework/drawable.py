from __future__ import annotations
from typing import Any, Self, TYPE_CHECKING
import pygame
import batFramework as bf
from .entity import Entity

if TYPE_CHECKING:
    from .group import Group


class Drawable(Entity):
    """
    Basic entity class
    """

    def __init__(
        self,
        size: None | tuple[int | float] = None,
        surface_flags: int = 0,
        convert_alpha: bool = False,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args,**kwargs)
        self.visible: bool = True
        self.draw_order: int = 0  # order among siblings in the scene or group (higher = drawn on top)
        self.draw_layer: str = bf.Layer.WORLD  # scene layer (camera), ignored inside a group
        if size is not None:
            self.rect.size = size
        self.convert_alpha: bool = convert_alpha
        self.surface_flags: int = surface_flags
        self.blit_flags: int = 0
        self._parent_group: Group | None = None  # set by Group.add / Group.remove
        self.surface: pygame.Surface = pygame.Surface(self.rect.size, surface_flags)
        if convert_alpha:
            self.surface = self.surface.convert_alpha()
            self.surface.fill((0, 0, 0, 0))

    @property
    def parent_group(self) -> Group | None:
        """The group drawing this entity (use Group.add / Group.remove to change it)"""
        return self._parent_group

    def kill(self):
        if self._parent_group is not None:
            self._parent_group.remove(self)
        else:
            super().kill()

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

    def get_camera(self) -> bf.Camera | None:
        """
        The camera this entity is drawn with: its group's, or the one of its layer in the scene.
        Use it for anything in the entity's own coordinate space (e.g. get_camera().get_mouse_pos()).
        """
        if self._parent_group is not None:
            return self._parent_group.get_camera()
        if self.parent_scene is not None:
            return self.parent_scene.get_camera(self.draw_layer)
        return None

    def set_draw_order(self, draw_order: int) -> Self:
        self.draw_order = draw_order
        if self._parent_group is not None:
            self._parent_group.request_draw_order_update()
        elif self.parent_scene is not None:
            self.parent_scene.request_draw_order_update()
        return self

    def set_draw_layer(self, layer: str) -> Self:
        """Scene layer to draw on (see bf.Layer). Ignored while in a group, which uses its own layer."""
        self.draw_layer = layer
        if self._parent_group is None and self.parent_scene is not None:
            self.parent_scene.request_draw_order_update()
        return self

    def set_visible(self, value: bool) -> Self:
        self.visible = value
        return self

    def get_mask(self) -> pygame.Mask:
        return pygame.mask.from_surface(self.surface)

    def mask_collide_point(self, point) -> bool:
        if not self.rect.collidepoint(point):
            return False
        mask = pygame.mask.from_surface(self.surface)
        x = point[0] - self.rect.x
        y = point[1] - self.rect.y
        return mask.get_at((x, y)) == 1

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

    def get_blit_data(
        self, camera: bf.Camera
    ) -> tuple[pygame.Surface, pygame.FRect] | None:
        """
        Return (surface, screen destination) to blit, or None if nothing should be drawn.
        Override this rather than draw when the entity is a single blit, so groups can batch it.
        """
        if (
            not self.visible
            or not camera.world_rect.colliderect(self.rect)
            or self.surface.get_alpha() == 0
        ):
            return None
        return self.surface, camera.world_to_screen(self.rect)

    def draw(self, camera: bf.Camera) -> None:
        """
        Draw the entity onto the camera surface
        """
        data = self.get_blit_data(camera)
        if data is not None:
            camera.surface.blit(*data, special_flags=self.blit_flags)

import pygame
from pygame.math import Vector2
import batFramework as bf
from typing import Self


class Camera:
    def __init__(
        self, flags=0, size: tuple[int, int] | None = None, convert_alpha: bool = False
    ) -> None:
        """
        Initialize the Camera object.

        Args:
            flags (int): Flags for camera initialization.
            size (tuple): Optional size for camera (defaults to window size)
            convert_alpha (bool): Convert surface to support alpha values
        """
        self.cached_surfaces: dict[tuple[int, int], pygame.Surface] = {}

        self.target_size = size if size else bf.const.RESOLUTION
        self.should_convert_alpha: bool = convert_alpha
        self.rect = pygame.FRect(0, 0, *self.target_size)
        self.vector_center = Vector2(0, 0)

        self.surface: pygame.Surface = pygame.Surface((0, 0))  # tmp dummy
        self.flags: int = flags | (pygame.SRCALPHA if convert_alpha else 0)
        self.blit_special_flags: int = pygame.BLEND_ALPHA_SDL2

        self._clear_color: pygame.Color = pygame.Color(0, 0, 0, 0)
        if not convert_alpha:
            self._clear_color = pygame.Color(0, 0, 0)

        self.follow_point_func = None
        self.follow_friction: float = 0.5

        self.zoom_factor = 1
        self.max_zoom = 2
        self.min_zoom = 0.1
        self.zoom(1)

    def set_clear_color(self, color: pygame.Color | tuple | str) -> Self:
        """
        Set the clear color for the camera surface.

        Args:
            color (pygame.Color | tuple): Color to set as the clear color.

        Returns:
            Camera: Returns the Camera object.
        """
        self._clear_color = color
        return self

    def set_max_zoom(self, value: float) -> Self:
        """
        Set the maximum zoom value for the camera.

        Args:
            value (float): Maximum zoom value.

        Returns:
            Camera: Returns the Camera object.
        """
        self.max_zoom = value
        return self

    def set_min_zoom(self, value: float) -> Self:
        """
        Set the minimum zoom value for the camera.

        Args:
            value (float): Minimum zoom value.

        Returns:
            Camera: Returns the Camera object.
        """
        self.min_zoom = value
        return self

    def clear(self) -> None:
        """
        Clear the camera surface with the set clear color.
        """
        self.surface.fill(self._clear_color)

    def get_center(self) -> tuple[float, float]:
        """
        Get the center of the camera's view.

        Returns:
            tuple[float,float]: Returns the center coordinates.
        """
        return self.rect.center

    def get_position(self) -> tuple[float, float]:
        """
        Get the center of the camera's view.

        Returns:
            tuple[float,float]: Returns the center coordinates.
        """
        return self.rect.topleft

    def move_by(self, x: float | int, y: float | int) -> Self:
        """
        Moves the camera rect by the given coordinates.

        Args:
            x: X-coordinate to move.
            y: Y-coordinate to move.

        Returns:
            Camera: Returns the Camera object.
        """
        self.rect.move_ip(x, y)
        return self

    def set_position(self, x, y) -> Self:
        """
        Set the camera rect top-left position.

        Args:
            x: X-coordinate to set.
            y: Y-coordinate to set.

        Returns:
            Camera: Returns the Camera object.
        """
        self.rect.topleft = (x, y)

        return self

    def set_center(self, x, y) -> Self:
        """
        Set the camera rect center position.

        Args:
            x: X-coordinate for the center.
            y: Y-coordinate for the center.

        Returns:
            Camera: Returns the Camera object.
        """
        self.rect.center = (x, y)
        return self

    def set_follow_point(self, func, follow_speed: float = 0.1) -> Self:
        """
        Set the following function (returns tuple x y).
        Camera will center its position to the center of the given coordinates.

        Args:
            func: Function returning coordinates to follow.

        Returns:
            Camera: Returns the Camera object.
        """
        self.follow_point_func = func
        self.follow_speed = follow_speed if func else 0.1
        return self

    def set_follow_friction(self,friction:float)->Self:
        self.follow_friction = friction
        return self

    def zoom_by(self, amount: float) -> Self:
        """
        Zooms the camera by the given amount.

        Args:
            amount (float): Amount to zoom.

        Returns:
            Camera: Returns the Camera object.
        """
        self.zoom(max(self.min_zoom, min(self.max_zoom, self.zoom_factor + amount)))
        return self

    def zoom(self, factor: float) -> Self:
        """
        Zooms the camera to the given factor.

        Args:
            factor: Factor to set for zooming.

        Returns:
            Camera: Returns the Camera object.
        """
        if factor < self.min_zoom or factor > self.max_zoom:
            print(
                f"Zoom value {factor} is outside the zoom range : [{self.min_zoom},{self.max_zoom}]"
            )
            return self

        factor = round(factor, 2)
        self.zoom_factor = factor
        new_res = tuple(round((i / factor) / 2) * 2 for i in self.target_size)
        self.surface = self._get_cached_surface(new_res)
        self.rect = self.surface.get_frect(center=self.rect.center)
        self.clear()
        return self

    def _free_cache(self):
        self.cached_surfaces = {}

    def _get_cached_surface(self, new_size: tuple[int, int]):
        surface = self.cached_surfaces.get(new_size, None)
        if surface is None:
            surface = pygame.Surface(new_size, flags=self.flags)
            if self.flags & pygame.SRCALPHA:
                surface = surface.convert_alpha()
            self.cached_surfaces[new_size] = surface

        return surface

    def resize(self, size: tuple[int, int] | None = None) -> Self:
        if size is None:
            size = bf.const.RESOLUTION
        self.target_size = size
        self.rect.center = (size[0] / 2, size[1] / 2)
        self.zoom(self.zoom_factor)

        return self

    def intersects(self, rect: pygame.Rect | pygame.FRect) -> bool:
        """
        Check if the camera view intersects with the given rectangle.

        Args:
            rect (pygame.Rect | pygame.FRect): Rectangle to check intersection with.

        Returns:
            bool: True if intersection occurs, False otherwise.
        """
        return self.rect.colliderect(rect)

    def world_to_screen(
        self, rect: pygame.Rect | pygame.FRect
    ) -> pygame.Rect | pygame.FRect:
        """
        world_to_screen the given rectangle coordinates relative to the camera.

        Args:
            rect (pygame.Rect | pygame.FRect): Rectangle to world_to_screen.

        Returns:
            pygame.FRect: Transposed rectangle.
        """
        return pygame.FRect(rect[0] - self.rect.left, rect[1] - self.rect.top, rect[2],rect[3])

    def world_to_screen_point(
        self, point: tuple[float, float] | tuple[int, int]
    ) -> tuple[float, float]:
        """
        world_to_screen the given 2D point coordinates relative to the camera.

        Args:
            point (tuple[float,float] | tuple[int,int]): Point to world_to_screen.

        Returns:
            tuple[float,float] : Transposed point.
        """
        return point[0] - self.rect.x, point[1] - self.rect.y

    def screen_to_world(
        self, point: tuple[float, float] | tuple[int, int]
    ) -> tuple[float, float]:
        """
        Convert screen coordinates to world coordinates based on camera settings.

        Args:
            point (tuple[float,float] | tuple[int,int]): Point to screen_to_world.
        Returns:
            tuple: Converted world coordinates.
        """
        return (
            point[0] / self.zoom_factor + self.rect.x,
            point[1] / self.zoom_factor + self.rect.y,
        )

    def update(self, dt):
        """
        Update the camera position based on the follow point function.

        Args:
            dt: Time delta for updating the camera position.
        """
        if self.follow_point_func:
            self.vector_center.update(*self.rect.center)
            amount = pygame.math.clamp(self.follow_friction,0,1)
            self.set_center(*self.vector_center.lerp(self.follow_point_func(), amount))

    def draw(self, surface: pygame.Surface):
        """
        Draw the camera view onto the provided surface with proper scaling.

        Args:
            surface (pygame.Surface): Surface to draw the camera view onto.
        """
        if self.zoom_factor == 1:
            surface.blit(self.surface, (0, 0), special_flags=self.blit_special_flags)
            # surface.blit(self.surface, (0, 0))
            return

        # Scale the surface to match the resolution
        scaled_surface = pygame.transform.scale(self.surface, self.target_size)
        surface.blit(scaled_surface, (0, 0), special_flags=self.blit_special_flags)

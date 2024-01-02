import pygame
from pygame.math import Vector2
import math
import batFramework as bf


class Camera:
    _transform_cache = {}  # Cache for transformed surfaces

    def __init__(self, flags=0, size: tuple[int,int] | None = None,convert_alpha:bool=False) -> None:
        """
        Initialize the Camera object.

        Args:
            flags (int): Flags for camera initialization.
            size (tuple): Optional size for camera (defaults to window size)
        """
        # Initialize camera attributes
        size = size if size else bf.const.RESOLUTION
        self.rect = pygame.Rect(0, 0, *size)
        self.flags: int = flags
        self.blit_special_flags: int = pygame.BLEND_ALPHA_SDL2
        self._clear_color: pygame.Color = pygame.Color(0, 0, 0, 0)
        self.zoom_factor = 1
        self.cached_surfaces: dict[float, pygame.Surface] = {}
        self.surface: pygame.Surface = pygame.Surface((0, 0))
        if convert_alpha : 
            self.surface = self.surface.convert_alpha()
        else:
            self.surface = self.surface.convert()
        self.follow_point_func = None
        self.max_zoom = 2
        self.min_zoom = 0.1
        self.zoom(1)

    def set_clear_color(self, color: pygame.Color | tuple | str) -> "Camera":
        """
        Set the clear color for the camera surface.

        Args:
            color (pygame.Color | tuple): Color to set as the clear color.

        Returns:
            Camera: Returns the Camera object.
        """
        if not isinstance(color, pygame.Color):
            color = pygame.Color(color)
        self._clear_color = color
        return self

    def set_max_zoom(self, value: float) -> "Camera":
        """
        Set the maximum zoom value for the camera.

        Args:
            value (float): Maximum zoom value.

        Returns:
            Camera: Returns the Camera object.
        """
        self.max_zoom = value
        return self

    def set_min_zoom(self, value: float) -> "Camera":
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

    def get_center(self) -> tuple[float,float]:
        """
        Get the center of the camera's view.

        Returns:
            Vector2: Returns the center coordinates.
        """
        return self.rect.center

    def move(self, x, y) -> "Camera":
        """
        Moves the camera rect by the given coordinates.

        Args:
            x: X-coordinate to move.
            y: Y-coordinate to move.

        Returns:
            Camera: Returns the Camera object.
        """
        self.rect.topleft += Vector2(x, y)
        return self

    def set_position(self, x, y) -> "Camera":
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

    def set_center(self, x, y) -> "Camera":
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

    def set_follow_point(self, func) -> "Camera":
        """
        Set the following function (returns tuple x y).
        Camera will center its position to the center of the given coordinates.

        Args:
            func: Function returning coordinates to follow.

        Returns:
            Camera: Returns the Camera object.
        """
        self.follow_point_func = func
        return self

    def zoom_by(self, amount: float) -> "Camera":
        """
        Zooms the camera by the given amount.

        Args:
            amount (float): Amount to zoom.

        Returns:
            Camera: Returns the Camera object.
        """
        self.zoom(self.zoom_factor + amount)
        return self

    def zoom(self, factor) -> "Camera":
        """
        Zooms the camera to the given factor.

        Args:
            factor: Factor to set for zooming.

        Returns:
            Camera: Returns the Camera object.
        """
        if factor < self.min_zoom or factor > self.max_zoom:
            return self

        factor = round(factor, 2)
        self.zoom_factor = factor

        if factor not in self.cached_surfaces:
            self.cached_surfaces[factor] = pygame.Surface(
                tuple(i / factor for i in bf.const.RESOLUTION), flags=self.flags
            ).convert_alpha()
            self.cached_surfaces[factor].fill((0, 0, 0, 0))

        self.surface = self.cached_surfaces[self.zoom_factor]
        self.rect = self.surface.get_rect(center=self.rect.center)
        return self

    def intersects(self, rect: pygame.Rect | pygame.FRect) -> bool:
        """
        Check if the camera view intersects with the given rectangle.

        Args:
            rect (pygame.Rect | pygame.FRect): Rectangle to check intersection with.

        Returns:
            bool: True if intersection occurs, False otherwise.
        """
        return (
            self.rect.x < rect.right
            and self.rect.right > rect.x
            and self.rect.y < rect.bottom
            and self.rect.bottom > rect.y
        )

    def transpose(self, rect: pygame.Rect | pygame.FRect) -> pygame.Rect | pygame.FRect:
        """
        Transpose the given rectangle coordinates relative to the camera.

        Args:
            rect (pygame.Rect | pygame.FRect): Rectangle to transpose.

        Returns:
            pygame.FRect: Transposed rectangle.
        """
        return pygame.FRect(rect.x - self.rect.left, rect.y - self.rect.top, *rect.size)

    def convert_screen_to_world(self, x, y):
        """
        Convert screen coordinates to world coordinates based on camera settings.

        Args:
            x: X-coordinate in screen space.
            y: Y-coordinate in screen space.

        Returns:
            tuple: Converted world coordinates.
        """
        return x / self.zoom_factor + self.rect.x, y / self.zoom_factor + self.rect.y

    def update(self, dt):
        """
        Update the camera position based on the follow point function.

        Args:
            dt: Time delta for updating the camera position.
        """
        if self.follow_point_func:
            target = self.follow_point_func()
            self.rect.center = Vector2(self.rect.center).lerp(target, ((dt * 60) * 0.1))

    def draw(self, surface: pygame.Surface):
        """
        Draw the camera view onto the provided surface with proper scaling.

        Args:
            surface (pygame.Surface): Surface to draw the camera view onto.
        """
        if self.zoom_factor == 1:
            surface.blit(self.surface, (0, 0), special_flags=self.blit_special_flags)
            return

        # Scale the surface to match the resolution
        scaled_surface = pygame.transform.scale(self.surface, bf.const.RESOLUTION)
        surface.blit(scaled_surface, (0, 0), special_flags=self.blit_special_flags)

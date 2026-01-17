from __future__ import annotations
import pygame
from pygame.math import Vector2
import batFramework as bf
from typing import Self
import math


class Camera:
    def __init__(
        self, flags=0, size: tuple[int, int] | None = None, convert_alpha: bool = False,fullscreen:bool=True
    ) -> None:
        self.cached_surfaces: dict[tuple[int, int], pygame.Surface] = {}
        self.fullscreen : bool = fullscreen # auto fill the screen (i.e react to VIDEORESIZE event)
        self.flags: int = flags | (pygame.SRCALPHA if convert_alpha else 0)
        self.blit_special_flags: int = pygame.BLEND_ALPHA_SDL2

        size = size if size else bf.const.RESOLUTION
        self.rect = pygame.FRect(0, 0, *size)
        self.transform_target_surface : pygame.Surface = pygame.Surface(self.rect.size,self.flags)
        self.should_convert_alpha: bool = convert_alpha
        self.world_rect = pygame.FRect(0, 0, *self.rect.size)

        self.vector_center = Vector2(0, 0)
        self.rotation = 0.0  # Rotation in degrees

        self.surface: pygame.Surface = pygame.Surface((0, 0))  # dynamic : create new at each new zoom value

        self._clear_color: pygame.typing.ColorLike = pygame.Color(0, 0, 0, 0) if convert_alpha else pygame.Color(0, 0, 0)

        self.follow_point_func = None
        self.damping = float("inf")
        self.dead_zone_radius = 10

        self.zoom_factor = 1
        self.max_zoom = 2
        self.min_zoom = 0.1
        self.zoom(1,force=True)

    def get_mouse_pos(self) -> tuple[float, float]:
        return self.screen_to_world(pygame.mouse.get_pos())

    def set_clear_color(self, color: pygame.Color | tuple | str) -> Self:
        self._clear_color = color
        return self

    def set_max_zoom(self, value: float) -> Self:
        self.max_zoom = value
        return self

    def set_min_zoom(self, value: float) -> Self:
        self.min_zoom = value
        return self

    def set_rotation(self, angle: float) -> Self:
        """
        Set the camera rotation in degrees.
        """
        self.rotation = angle % 360
        return self
    
    def rotate_by(self,angle:float)->Self:
        """
        Increment rotation by given angle in degrees.
        """
        self.rotation+=angle
        self.rotation%=360
        return self

    def clear(self) -> None:
        if self._clear_color is None:
            return
        self.surface.fill(self._clear_color)

    def get_center(self) -> tuple[float, float]:
        return self.world_rect.center

    def get_position(self) -> tuple[float, float]:
        return self.world_rect.topleft

    def move_by(self, x: float | int, y: float | int) -> Self:
        # self.world_rect.move_ip(x, y)
        self.world_rect.x += x
        self.world_rect.y += y
        return self

    def set_position(self, x, y) -> Self:
        self.world_rect.topleft = (x, y)
        return self

    def set_center(self, x, y) -> Self:
        self.world_rect.center = (x, y)
        return self

    def set_follow_point_func(self, func) -> Self:
        self.follow_point_func = func
        return self

    def set_follow_speed(self, speed: float) -> Self:
        self.follow_speed = speed
        return self

    def set_follow_damping(self, damping: float) -> Self:
        self.damping = damping
        return self

    def set_dead_zone_radius(self, radius: float) -> Self:
        self.dead_zone_radius = radius
        return self

    def zoom_by(self, amount: float) -> Self:
        return self.zoom(self.zoom_factor + amount)

    def zoom(self, factor: float,force:bool=False) -> Self:
        clamped = max(self.min_zoom, min(self.max_zoom, round(factor, 2)))
        if clamped == self.zoom_factor and not force:
            return self

        self.zoom_factor = clamped
        new_res = tuple([round((i / clamped) / 2) * 2 for i in self.rect.size])

        if self.surface.get_size() != new_res:
            self.surface = self._get_cached_surface((new_res[0],new_res[1]))

        self.world_rect = self.surface.get_frect(center=self.world_rect.center)
        self.clear()
        return self

    def _free_cache(self):
        self.cached_surfaces.clear()

    def _get_cached_surface(self, new_size: tuple[int, int]):
        surface = self.cached_surfaces.get(new_size)
        if surface is None:
            surface = pygame.Surface(new_size, flags=self.flags)
            # if self.flags & pygame.SRCALPHA:
            #     surface = surface.convert_alpha()
            self.cached_surfaces[new_size] = surface
        return surface

    def set_size(self, size: tuple[int, int] | None = None) -> Self:
        if size is None:
            size = bf.const.RESOLUTION
        center = self.rect.center
        self.rect.size = size
        self.rect.center = center
        self.transform_target_surface = pygame.Surface(self.rect.size,self.flags)
        self.world_rect.center = (size[0] / 2, size[1] / 2)
        self.zoom(self.zoom_factor)
        return self

    def intersects(self, rect: pygame.Rect | pygame.FRect) -> bool:
        return self.world_rect.colliderect(rect)

    def world_to_screen(self, rect: pygame.Rect | pygame.FRect) -> pygame.FRect:
        return pygame.FRect(
            (rect[0] - self.world_rect.left), (rect[1] - self.world_rect.top), rect[2], rect[3]
        )

    def world_to_screen_scaled(self, rect: pygame.Rect | pygame.FRect) -> pygame.FRect:
        screen_rect = self.world_to_screen(rect)
        return pygame.FRect(
            screen_rect.x * self.zoom_factor,
            screen_rect.y * self.zoom_factor,
            screen_rect.w * self.zoom_factor,
            screen_rect.h * self.zoom_factor,
        )

    def world_to_screen_point(self, point: tuple[float, float] | tuple[int, int]) -> tuple[float, float]:
        return (
            (point[0] - self.world_rect.x),
            (point[1] - self.world_rect.y),
        )

    def world_to_screen_point_scaled(self, point: tuple[float, float] | tuple[int, int]) -> tuple[float, float]:
        return (
            (point[0] - self.world_rect.x) * self.zoom_factor,
            (point[1] - self.world_rect.y) * self.zoom_factor,
        )


    def screen_to_world(self, point: tuple[float, float] | tuple[int, int]) -> tuple[float, float]:
        """
        roates, scales and translates point to world coordinates

        """
        # Center of the screen (zoomed+rotated surface)
        cx, cy = self.rect.w / 2, self.rect.h / 2

        # Offset from center
        dx, dy = point[0] - cx, point[1] - cy

        # rotate that offset
        if self.rotation != 0:
            angle_rad = math.radians(self.rotation)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            dx, dy = cos_a * dx - sin_a * dy, sin_a * dx + cos_a * dy

        # Un-zoom and add camera position
        wx = (dx + cx) / self.zoom_factor + self.world_rect.x
        wy = (dy + cy) / self.zoom_factor + self.world_rect.y
        return wx, wy


    def update(self, dt: float):
        if not self.follow_point_func or not (math.isfinite(dt) and dt > 0):
            return

        target = Vector2(self.follow_point_func())
        self.vector_center.xy.update(self.world_rect.center)

        if self.damping == float("inf"):
            self.vector_center.xy = target.xy
        elif math.isfinite(self.damping) and self.damping > 0:
            damping_factor = 1 - math.exp(-self.damping * dt)
            if not math.isnan(damping_factor):
                diff = target - self.vector_center
                self.vector_center += diff * damping_factor

        self.world_rect.center = self.vector_center


    def draw(self, surface: pygame.Surface):
        """
        Draw the camera view onto the provided surface with proper scaling and rotation.

        Args:
            surface (pygame.Surface): Surface to draw the camera view onto.
        """
        # Scale the camera surface to the target size
        if self.zoom_factor == 1 and self.rotation == 0:
            surface.blit(self.surface, (0, 0), special_flags=self.blit_special_flags)
            return

        pygame.transform.scale(self.surface, self.rect.size, self.transform_target_surface)

        result_surface = self.transform_target_surface

        if self.rotation != 0:
            # Rotate around the center of the target surface
            rotated_surface = pygame.transform.rotate(result_surface, self.rotation)
            rect = rotated_surface.get_rect(center=(self.rect.w // 2, self.rect.h // 2))
            surface.blit(rotated_surface, rect.topleft, special_flags=self.blit_special_flags)
        else:
            surface.blit(result_surface, (0, 0), special_flags=self.blit_special_flags)
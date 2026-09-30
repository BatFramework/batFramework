from __future__ import annotations
import pygame
from pygame.math import Vector2
import batFramework as bf
from typing import Self
import math


class Camera:
    def __init__(
        self,
        flags=0,
        size: tuple[int, int] | None = None,
        convert_alpha: bool = False,
        fullscreen: bool = True,
    ) -> None:
        self.cached_surfaces: dict[tuple[int, int], pygame.Surface] = {}
        self.fullscreen: bool = fullscreen
        self.flags: int = flags | (pygame.SRCALPHA if convert_alpha else 0)
        self.blit_special_flags: int = pygame.BLEND_ALPHA_SDL2

        size = size if size else bf.const.RESOLUTION
        self.rect = pygame.FRect(0, 0, *size)
        self.transform_target_surface: pygame.Surface = pygame.Surface(
            self.rect.size, self.flags
        )
        self.should_convert_alpha: bool = convert_alpha
        self.world_rect = pygame.FRect(0, 0, *self.rect.size)

        # Flat-float cache of world_rect.x/y — avoids C-extension attribute
        # lookup in the coordinate-transform hot path (called per widget/frame).
        # Must be kept in sync wherever world_rect position changes.
        self._world_x: float = 0.0
        self._world_y: float = 0.0

        self.vector_center = Vector2(0, 0)
        self._follow_target = Vector2(0, 0)  # reused in update — avoids per-frame alloc
        self.rotation = 0.0

        self.surface: pygame.Surface = pygame.Surface((0, 0))

        self.clear_color: pygame.typing.ColorLike = (
            pygame.Color(0, 0, 0, 0) if convert_alpha else pygame.Color(0, 0, 0)
        )

        self.follow_point_func = None
        self.damping = float("inf")
        self._damping_is_inf: bool = True   # cached — updated in set_follow_damping
        self.dead_zone_radius: float = 0  # target can move this far from the center before the camera follows
        self.follow_speed: float = float("inf")  # max follow speed in world units per second

        self.zoom_factor = 1
        self.max_zoom = 2
        self.min_zoom = 0.1

        # Cached trig — updated in set_rotation, avoids recompute on mouse events
        self._cos_r: float = 1.0
        self._sin_r: float = 0.0

        # Cached half-screen dimensions — updated in set_size
        self._half_w: float = self.rect.w / 2
        self._half_h: float = self.rect.h / 2

        # Cached render surface -> screen transform — updated in zoom
        # (the effective scale can differ slightly from zoom_factor because
        # the render size is rounded to whole pixels)
        self._render_half_w: float = self._half_w
        self._render_half_h: float = self._half_h
        self._scale_x: float = 1.0
        self._scale_y: float = 1.0

        self.zoom(1, force=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sync_world_pos(self) -> None:
        """Pull world_rect.x/y into the flat-float cache after any move."""
        self._world_x = self.world_rect.x
        self._world_y = self.world_rect.y

    # ------------------------------------------------------------------
    # Mouse
    # ------------------------------------------------------------------

    def get_mouse_pos(self) -> tuple[float, float]:
        return self.screen_to_world(pygame.mouse.get_pos())

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------


    def set_max_zoom(self, value: float) -> Self:
        self.max_zoom = value
        return self

    def set_min_zoom(self, value: float) -> Self:
        self.min_zoom = value
        return self

    def set_follow_point_func(self, func) -> Self:
        """func returns the world point the camera center should follow"""
        self.follow_point_func = func
        return self

    def set_follow_speed(self, speed: float) -> Self:
        """Max follow speed in world units per second (inf = no limit)"""
        self.follow_speed = speed
        return self

    def set_follow_damping(self, damping: float) -> Self:
        """Higher follows tighter, inf snaps to the target"""
        self.damping = damping
        self._damping_is_inf = (damping == float("inf"))
        return self

    def set_dead_zone_radius(self, radius: float) -> Self:
        """Distance the target can move from the center before the camera follows"""
        self.dead_zone_radius = radius
        return self

    # ------------------------------------------------------------------
    # Rotation
    # ------------------------------------------------------------------

    def _render_size(self) -> tuple[int, int]:
        """
        Render surface size for the current zoom and rotation.
        At rotation=0: screen size / zoom, rounded to even pixels
        (exactly the screen size at zoom 1).
        At any other angle: a square whose side equals ceil(sqrt(w²+h²))
        so no content is ever clipped regardless of angle.
        """
        if self.zoom_factor == 1:
            base_w, base_h = int(self.rect.w), int(self.rect.h)
        else:
            base_w = max(2, round((self.rect.w / self.zoom_factor) / 2) * 2)
            base_h = max(2, round((self.rect.h / self.zoom_factor) / 2) * 2)

        if self.rotation == 0:
            return (base_w, base_h)

        # x * x is faster than x ** 2 — avoids __pow__ dispatch
        diag = math.ceil(math.sqrt(base_w * base_w + base_h * base_h))
        diag += diag % 2    # round up to even
        return (diag, diag)

    def set_rotation(self, angle: float) -> Self:
        new_rotation = angle % 360
        if new_rotation == self.rotation:
            return self
        self.rotation = new_rotation
        angle_rad = math.radians(new_rotation)
        self._cos_r = math.cos(angle_rad)
        self._sin_r = math.sin(angle_rad)
        self.zoom(self.zoom_factor, force=True)
        return self

    def rotate_by(self, angle: float) -> Self:
        return self.set_rotation(self.rotation + angle)

    # ------------------------------------------------------------------
    # Zoom / size
    # ------------------------------------------------------------------

    def zoom_by(self, amount: float) -> Self:
        return self.zoom(self.zoom_factor + amount)

    def zoom(self, factor: float, force: bool = False) -> Self:
        clamped = max(self.min_zoom, min(self.max_zoom, round(factor, 2)))
        if clamped == self.zoom_factor and not force:
            return self

        self.zoom_factor = clamped
        new_res = self._render_size()

        if self.surface.get_size() != new_res:
            self.surface = self._get_cached_surface(new_res)

        self.world_rect = self.surface.get_frect(center=self.world_rect.center)
        self._sync_world_pos()
        self._update_render_transform()
        self.clear()
        return self

    def _update_render_transform(self) -> None:
        """Cache how the render surface maps onto the screen (see draw)."""
        sw, sh = self.surface.get_size()
        self._render_half_w = sw / 2
        self._render_half_h = sh / 2
        if self.rotation == 0:
            # the render surface is stretched to the screen size
            self._scale_x = self.rect.w / sw
            self._scale_y = self.rect.h / sh
        else:
            # rotozoom scales uniformly by zoom_factor
            self._scale_x = self._scale_y = self.zoom_factor

    def _free_cache(self) -> None:
        self.cached_surfaces.clear()

    def _get_cached_surface(self, new_size: tuple[int, int]) -> pygame.Surface:
        surface = self.cached_surfaces.get(new_size)
        if surface is None:
            surface = pygame.Surface(new_size, flags=self.flags)
            self.cached_surfaces[new_size] = surface
        return surface

    def set_size(self, size: tuple[int, int] | None = None) -> Self:
        if size is None:
            size = bf.const.RESOLUTION
        center = self.rect.center
        self.rect.size = size
        self.rect.center = center
        self._half_w = size[0] / 2
        self._half_h = size[1] / 2
        self.transform_target_surface = pygame.Surface(self.rect.size, self.flags)
        # rebuild the render surface for the new size, keeping the camera center
        self.zoom(self.zoom_factor, force=True)
        return self

    # ------------------------------------------------------------------
    # Camera movement
    # ------------------------------------------------------------------

    def clear(self) -> None:
        if self.clear_color is None:
            return
        self.surface.fill(self.clear_color)

    def get_center(self) -> tuple[float, float]:
        return self.world_rect.center

    def get_position(self) -> tuple[float, float]:
        return self.world_rect.topleft

    def move_by(self, x: float | int, y: float | int) -> Self:
        self._world_x += x
        self._world_y += y
        self.world_rect.x = self._world_x
        self.world_rect.y = self._world_y
        return self

    def set_position(self, x: float, y: float) -> Self:
        self._world_x = x
        self._world_y = y
        self.world_rect.topleft = (x, y)
        return self

    def set_center(self, x: float, y: float) -> Self:
        self.world_rect.center = (x, y)
        self._sync_world_pos()
        return self

    def intersects(self, rect: pygame.Rect | pygame.FRect) -> bool:
        return self.world_rect.colliderect(rect)

    # ------------------------------------------------------------------
    # Coordinate transforms  (hot path — called per widget per frame)
    # _world_x/_world_y used instead of self.world_rect.x/y to avoid
    # C-extension attribute lookup on every call.
    # ------------------------------------------------------------------

    def world_to_screen(self, rect: pygame.Rect | pygame.FRect) -> pygame.FRect:
        return pygame.FRect(
            rect[0] - self._world_x,
            rect[1] - self._world_y,
            rect[2],
            rect[3],
        )

    def world_to_screen_scaled(self, rect: pygame.Rect | pygame.FRect) -> pygame.FRect:
        """
        World rect to final screen coordinates (after zoom and rotation).
        When rotated, the result is the rect's size scaled, centered on its
        transformed center (the rotated rect itself is not axis aligned).
        """
        w, h = rect[2] * self._scale_x, rect[3] * self._scale_y
        cx, cy = self.world_to_screen_point_scaled(
            (rect[0] + rect[2] / 2, rect[1] + rect[3] / 2)
        )
        return pygame.FRect(cx - w / 2, cy - h / 2, w, h)

    def world_to_screen_point(
        self, point: tuple[float, float] | tuple[int, int]
    ) -> tuple[float, float]:
        return (point[0] - self._world_x, point[1] - self._world_y)

    def world_to_screen_point_scaled(
        self, point: tuple[float, float] | tuple[int, int]
    ) -> tuple[float, float]:
        """World point to final screen coordinates (after zoom and rotation)."""
        # offset from the render surface center, scaled to screen pixels
        dx = (point[0] - self._world_x - self._render_half_w) * self._scale_x
        dy = (point[1] - self._world_y - self._render_half_h) * self._scale_y
        if self.rotation != 0:
            # rotozoom rotates counter-clockwise on screen (y down)
            dx, dy = (
                self._cos_r * dx + self._sin_r * dy,
                -self._sin_r * dx + self._cos_r * dy,
            )
        return (dx + self._half_w, dy + self._half_h)

    def screen_to_world(
        self, point: tuple[float, float] | tuple[int, int]
    ) -> tuple[float, float]:
        """Rotates, scales and translates a screen point to world coordinates."""
        # the screen center always shows the render surface center (see draw)
        dx, dy = point[0] - self._half_w, point[1] - self._half_h

        if self.rotation != 0:
            dx, dy = (
                self._cos_r * dx - self._sin_r * dy,
                self._sin_r * dx + self._cos_r * dy,
            )

        return (
            self._world_x + self._render_half_w + dx / self._scale_x,
            self._world_y + self._render_half_h + dy / self._scale_y,
        )

    # ------------------------------------------------------------------
    # Update / follow
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if not self.follow_point_func or not (math.isfinite(dt) and dt > 0):
            return

        self._follow_target.update(self.follow_point_func())
        # start from the current center, so manual moves (set_center, move_by...) are kept
        self.vector_center.update(self.world_rect.center)
        delta = self._follow_target - self.vector_center

        # dead zone: only follow by how far the target is outside the radius
        distance = delta.length()
        if distance <= self.dead_zone_radius:
            return
        if self.dead_zone_radius > 0:
            delta.scale_to_length(distance - self.dead_zone_radius)

        if not self._damping_is_inf:
            # framerate independent exponential smoothing
            delta *= 1.0 - math.exp(-self.damping * dt)

        max_step = self.follow_speed * dt
        if delta.length_squared() > max_step * max_step:
            delta.scale_to_length(max_step)

        self.vector_center += delta
        self.world_rect.center = self.vector_center
        self._sync_world_pos()

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        rotation = self.rotation
        zoom = self.zoom_factor
        flags = self.blit_special_flags

        # Fast path (render surface is exactly the screen size)
        if rotation == 0 and self._scale_x == 1 and self._scale_y == 1:
            surface.blit(self.surface, (0, 0), special_flags=flags)
            return

        if rotation != 0:
            # # Rotate first, scale uniformly via rotozoom
            # rotated = pygame.transform.rotozoom(self.surface, rotation, zoom)

            # rw, rh = rotated.get_size()
            # surface.blit(
            #     rotated,
            #     (self._half_w - rw * 0.5, self._half_h - rh * 0.5),
            #     special_flags=flags,
            # )
            rotated = pygame.transform.rotate(self.surface, rotation)
            scaled_size = (
                round(rotated.get_width() * zoom),
                round(rotated.get_height() * zoom),
            )
            transformed = pygame.transform.scale(rotated, scaled_size)
            rw, rh = transformed.get_size()
            surface.blit(
                transformed,
                (self._half_w - rw * 0.5, self._half_h - rh * 0.5),
                special_flags=flags,
            )
        else:
            # Zoom only (uniform scale)
            pygame.transform.scale(
                self.surface, self.rect.size, self.transform_target_surface
            )
            surface.blit(self.transform_target_surface, (0, 0), special_flags=flags)

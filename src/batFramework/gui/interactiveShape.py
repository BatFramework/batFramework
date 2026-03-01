from __future__ import annotations
from .shape import Shape
from .interactiveWidget import InteractiveWidget
import pygame
import batFramework as bf
from typing import Self
from math import cos, ceil


class InteractiveShape(Shape, InteractiveWidget):
    """
    Combines Shape (rendering) with InteractiveWidget (logic) and adds all
    visual/audio feedback: hover & focus effects, disabled tinting, cursors,
    and focus/lose-focus sounds.

    Subclass this instead of inheriting from both Shape and InteractiveWidget
    directly whenever you need the full visual treatment.
    """

    def __init__(self, *args, **kwargs) -> None:
        self._focus_effect_cache: dict = {}
        self._hover_effect_cache: dict = {}

        # Cursors
        self.hover_cursor = bf.const.DEFAULT_HOVER_CURSOR
        self.click_cursor = bf.const.DEFAULT_CLICK_CURSOR

        # Sounds
        self.get_focus_sound: str | None = None
        self.lose_focus_sound: str | None = None

        super().__init__(*args, **kwargs)

    # -------------------------------------------------------------------------
    # Cursor / sound setters
    # -------------------------------------------------------------------------

    def set_hover_cursor(self, cursor: pygame.Cursor) -> Self:
        self.hover_cursor = cursor
        return self

    def set_click_cursor(self, cursor: pygame.Cursor) -> Self:
        self.click_cursor = cursor
        return self

    def set_get_focus_sound(self, sound_name: str) -> Self:
        self.get_focus_sound = sound_name
        return self

    def set_lose_focus_sound(self, sound_name: str) -> Self:
        self.lose_focus_sound = sound_name
        return self

    # -------------------------------------------------------------------------
    # Focus / hover visual helpers
    # -------------------------------------------------------------------------

    def _get_surface_filter(self, intensity:float=0.1) -> pygame.Surface:
        """Silhouette surface used for hover (add) and disabled (sub) blending."""
        size = int(self.rect.w), int(self.rect.h)
        key = (size, *self.border_radius)
        color = [int(max(0,min(255*intensity,255))) ]*3
        surface_filter = self._hover_effect_cache.get(key)
        if surface_filter is None:
            mask = pygame.mask.from_surface(self.surface, threshold=0)
            surface_filter = mask.to_surface(
                setcolor=color, unsetcolor=(0, 0, 0)
            )
            self._hover_effect_cache[key] = surface_filter
        return surface_filter

    def _paint_disabled(self) -> None:
        self.surface.blit(
            self._get_surface_filter(intensity=0.5), (0, 0), special_flags=pygame.BLEND_RGB_SUB
        )

    def _paint_hovered(self) -> None:
        self.surface.blit(
            self._get_surface_filter(), (0, 0), special_flags=pygame.BLEND_RGB_ADD
        )

    def paint(self) -> None:
        super().paint()  # Shape.paint() handles the base drawing
        if not self.is_enabled:
            self._paint_disabled()
        elif self.is_hovered:
            self._paint_hovered()

    def draw_focused(self, camera: bf.Camera) -> None:
        """Animated pulsing focus ring drawn in screen space."""
        prop = 8
        pulse = int(prop * 0.75 - (prop * cos(pygame.time.get_ticks() / 100) / 4))
        delta = (pulse // 2) * 2  # keep even

        screen_rect = camera.world_to_screen(
            self.rect.inflate(prop + self.outline_width, prop + self.outline_width)
        )

        inner = screen_rect.inflate(-delta, -delta)
        inner.topleft = 0, 0
        inner.w = ceil(inner.w) + 1
        inner.h = ceil(inner.h) + 1

        surface = self._focus_effect_cache.get(inner.size)
        if surface is None:
            surface = pygame.Surface(inner.size)
            self._focus_effect_cache[inner.size] = surface

        surface.set_colorkey((255, 0, 255))
        surface.fill((255, 0, 255))
        pygame.draw.rect(surface, "white", inner, 2, *self.border_radius)

        # Horizontal and vertical cross-cuts to form a bracket-style ring
        pygame.draw.rect(
            surface,
            (255, 0, 255),
            inner.inflate(-1 * (min(16, int(inner.w * 0.75)) & ~1), 0),
            2,
        )
        pygame.draw.rect(
            surface,
            (255, 0, 255),
            inner.inflate(0, -1 * (min(16, int(inner.h * 0.75)) & ~1)),
            2,
        )

        inner.center = screen_rect.center
        camera.surface.blit(surface, inner)

    # -------------------------------------------------------------------------
    # Cache invalidation
    # -------------------------------------------------------------------------

    def _resize_surface(self):
        res = super()._resize_surface()
        if res:
            self._focus_effect_cache.clear()
            self._hover_effect_cache.clear()
        return res

    # -------------------------------------------------------------------------
    # Event overrides — add visual/audio side-effects on top of logic
    # -------------------------------------------------------------------------

    def on_get_focus(self, focus_area: pygame.Rect = None) -> None:
        super().on_get_focus(focus_area)
        if self.get_focus_sound and self.parent_layer and self.parent_layer.scene.is_visible():
            bf.AudioManager().play_sound(self.get_focus_sound)

    def on_lose_focus(self) -> None:
        super().on_lose_focus()
        if self.lose_focus_sound and self.parent_layer and self.parent_layer.scene.is_visible():
            bf.AudioManager().play_sound(self.lose_focus_sound)

    def on_enter(self) -> None:
        super().on_enter()  # sets is_hovered, dirty_surface, calls do_on_enter
        if not self.is_enabled:
            return
        pygame.mouse.set_cursor(self.hover_cursor)

    def on_exit(self) -> None:
        super().on_exit()  # clears is_hovered, is_clicked_down, dirty_surface, calls do_on_exit
        pygame.mouse.set_cursor(bf.const.DEFAULT_CURSOR)
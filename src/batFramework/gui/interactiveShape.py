from __future__ import annotations
from .shape import Shape
from .interactiveWidget import InteractiveWidget
import pygame
import batFramework as bf
from ..camera import Camera
from typing import Self,Callable,Any
from types import MethodType
from math import cos, ceil, sin
from contextlib import contextmanager


class FocusIndicator:

    def default_pulse(self, camera: Camera) -> None:
        """Animated pulsing focus ring drawn in screen space."""

        screen_rect = camera.world_to_screen(self.rect)

        deltax = ceil( sin(pygame.time.get_ticks() / 150))
        deltay = ceil( sin(pygame.time.get_ticks() / 150))
        
        if self.rect.w %2 != 0:
            deltax += 1

        if self.rect.h %2 != 0:
            deltay += 1

        pygame.draw.rect(
            camera.surface,
            bf.color.BLUE,
            screen_rect.inflate(4+2*deltax, 4+2*deltay),
            width=2,
            border_radius=self.border_radius[0]+2 if self.border_radius else 0,
        )

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
        self._suppress_sounds: bool = False

        # Cursors
        self.hover_cursor = bf.const.DEFAULT_HOVER_CURSOR
        self.click_cursor = bf.const.DEFAULT_CLICK_CURSOR

        # Sounds
        self.get_focus_sound: str | None = None
        self.lose_focus_sound: str | None = None
        self.draw_focused : Callable[["InteractiveShape",Camera], None] = None
        self.set_focus_effect(FocusIndicator.default_pulse)

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

    @contextmanager
    def silent(self):
        """Suppress focus/click sounds for the duration of the block.

        Use when triggering focus or clicks programmatically so that
        sounds only play in response to actual user input::

            with play_button.silent():
                play_button.ask_focus()
        """
        self._suppress_sounds = True
        try:
            yield self
        finally:
            self._suppress_sounds = False

    # -------------------------------------------------------------------------
    # Focus / hover visual helpers
    # -------------------------------------------------------------------------


    def set_focus_effect(self, effect_func: Callable[["InteractiveShape",Camera], None] | None) -> Self:
        """
        Set a custom focus effect function. The function should take two arguments: 
        the InteractiveShape instance and the Camera instance, 
        and should handle drawing the desired focus effect in screen space.
        """
        if effect_func is None:
            self.draw_focused = None
        else:
            self.draw_focused = MethodType(effect_func, self)
        return self

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
            self._get_surface_filter(intensity=0.5), self._get_elevated_rect().topleft, special_flags=pygame.BLEND_RGB_SUB
        )

    def _paint_hovered(self) -> None:
        self.surface.blit(
            self._get_surface_filter(), self._get_elevated_rect().topleft, special_flags=pygame.BLEND_RGB_ADD
        )

    def paint(self) -> None:
        super().paint()  # Shape.paint() handles the base drawing
        if not self.is_enabled:
            self._paint_disabled()
        elif self.is_hovered or self.is_focused:
            self._paint_hovered()


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
        self.dirty_surface = True
        if self.get_focus_sound and not self._suppress_sounds and self.parent_scene and self.parent_scene.is_visible():
            bf.AudioManager().play_sound(self.get_focus_sound)

    def on_lose_focus(self) -> None:
        super().on_lose_focus()
        self.dirty_surface = True

        if self.lose_focus_sound and not self._suppress_sounds and self.parent_scene and self.parent_scene.is_visible():
            bf.AudioManager().play_sound(self.lose_focus_sound)

    def on_enter(self) -> None:
        super().on_enter()  # sets is_hovered, dirty_surface, calls do_on_enter
        if not self.is_enabled:
            return
        pygame.mouse.set_cursor(self.hover_cursor)

    def on_exit(self) -> None:
        super().on_exit()  # clears hover and updates press state, calls do_on_exit
        pygame.mouse.set_cursor(bf.const.DEFAULT_CURSOR)

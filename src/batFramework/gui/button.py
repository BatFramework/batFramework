from .label import Label
import batFramework as bf
from typing import Self, Callable
from .interactiveWidget import InteractiveWidget
import pygame
from math import ceil


class Button(Label, InteractiveWidget):
    _cache: dict = {}

    def __init__(self, text: str, callback: None | Callable = None) -> None:
        self.callback = callback
        self.is_hovered: bool = False
        self.effect_max: float = 20
        self.use_effect: bool = False
        self.effect_speed: float = 1.8
        self.is_clicking: bool = False
        self.effect: float = 0
        self.effect_color: tuple[int, int, int] | str = "white"
        self.enabled: bool = True
        self.hover_cursor = bf.const.DEFAULT_HOVER_CURSOR
        self.click_cursor = bf.const.DEFAULT_CLICK_CURSOR
        self.click_down_sound = None
        self.click_up_sound = None

        self.get_focus_sound = None
        self.lose_focus_sound = None
        super().__init__(text=text)
        self.set_debug_color("cyan")
        self.focusable = True

    def set_click_down_sound(self, sound_name: str) -> Self:
        self.click_down_sound = sound_name
        return self

    def set_click_up_sound(self, sound_name: str) -> Self:
        self.click_up_sound = sound_name
        return self

    def set_get_focus_sound(self, sound_name: str) -> Self:
        self.get_focus_sound = sound_name
        return self

    def set_lose_focus_sound(self, sound_name: str) -> Self:
        self.lose_focus_sound = sound_name
        return self

    def set_hover_cursor(self, cursor: pygame.Cursor) -> Self:
        self.hover_cursor = cursor
        return self

    def set_click_cursor(self, cursor: pygame.Cursor) -> Self:
        self.click_cursor = cursor
        return self

    def enable_effect(self) -> Self:
        self.use_effect = True
        return self

    def disable_effect(self) -> Self:
        self.use_effect = False
        self.effect = 0
        return self

    def set_effect_color(self, color: tuple[int, int, int] | str):
        self.effect_color = color
        return self

    def get_relief(self) -> int:
        if not self.relief:
            return 0
        return self.relief if not self.is_clicking else max(1, ceil(self.relief / 4))

    def get_surface_filter(self) -> pygame.Surface | None:
        size = self.surface.get_size()
        surface_filter = Button._cache.get((size, *self.border_radius), None)
        if surface_filter is None:
            # Create a mask from the original surface
            mask = pygame.mask.from_surface(self.surface, threshold=0)

            silhouette_surface = mask.to_surface(
                setcolor=(30, 30, 30), unsetcolor=(255, 255, 255)
            )

            Button._cache[(size, *self.border_radius)] = silhouette_surface

            surface_filter = silhouette_surface

        return surface_filter

    def enable(self) -> Self:
        self.enabled = True
        self.dirty_surface = True
        return self

    def disable(self) -> Self:
        self.enabled = False
        self.dirty_surface = True
        
        return self

    def is_enabled(self) -> bool:
        return self.enabled

    def set_callback(self, callback: Callable) -> Self:
        self.callback = callback
        return self

    def on_get_focus(self):
        v = self.is_focused
        super().on_get_focus()
        if self.is_focused != v:
            bf.AudioManager().play_sound(self.get_focus_sound)
        self.dirty_surface = True


    def on_lose_focus(self):
        v = self.is_focused
        super().on_lose_focus()
        if self.is_focused != v:
            bf.AudioManager().play_sound(self.lose_focus_sound)
        self.dirty_surface = True


    def to_string_id(self) -> str:
        return f"Button({self.text}){'' if self.enabled else '[disabled]'}"

    def click(self, force=False) -> None:
        if not self.enabled and not force:
            return
        if self.callback is not None:
            self.callback()
            bf.Timer(duration=0.1, end_callback=self._safety_effect_end).start()

    def _safety_effect_end(self) -> None:
        if self.effect > 0:
            self.effect = 0
            self.dirty_surface = True

    def start_effect(self):
        if self.effect <= 0:
            self.effect = self.effect_max

    def do_on_click_down(self, button) -> None:
        if self.enabled and button == 1 and self.effect == 0:
            if not self.get_focus():
                return
            self.is_clicking = True
            bf.AudioManager().play_sound(self.click_down_sound)

            pygame.mouse.set_cursor(self.click_cursor)

            if self.use_effect:
                self.start_effect()
            else:
                self.dirty_surface = True

    def do_on_click_up(self, button) -> None:
        if self.enabled and button == 1 and self.is_clicking:
            self.is_clicking = False
            bf.AudioManager().play_sound(self.click_up_sound)

            self.dirty_surface = True
            self.click()

    def on_enter(self) -> None:
        if not self.enabled:
            return
        super().on_enter()
        self.effect = 0
        self.dirty_surface = True
        pygame.mouse.set_cursor(self.hover_cursor)

    def on_exit(self) -> None:
        super().on_exit()
        self.is_clicking = False
        self.dirty_surface = True
        pygame.mouse.set_cursor(bf.const.DEFAULT_CURSOR)

    def on_lose_focus(self):
        super().on_lose_focus()
        self.on_exit()

    def on_key_down(self, key):
        if key == pygame.K_SPACE:
            self.on_click_down(1)
        super().on_key_down(key)

    def on_key_up(self, key):
        if key == pygame.K_SPACE:
            self.on_click_up(1)
        super().on_key_up(key)

    def update(self, dt):
        super().update(dt)
        if self.effect <= 0 or (not self.use_effect):
            return
        self.effect -= dt * 60 * self.effect_speed
        if self.is_clicking:
            if self.effect < 1:
                self.effect = 1
        else:
            if self.effect < 0:
                self.effect = 0
        self.dirty_surface = True

    def _paint_effect(self) -> None:
        if self.effect < 1:
            return
        e = int(min(self.rect.w // 3, self.rect.h // 3, self.effect))
        pygame.draw.rect(
            self.surface,
            self.effect_color,
            (
                0,
                self.relief - self.get_relief(),
                self.rect.w,
                self.rect.h - self.relief,
            ),
            # int(self.effect),
            e,
            *self.border_radius,
        )

    def _paint_disabled(self) -> None:
        self.surface.blit(
            self.get_surface_filter(), (0, 0), special_flags=pygame.BLEND_RGB_SUB
        )

    def _paint_hovered(self) -> None:
        self.surface.blit(
            self.get_surface_filter(), (0, 0), special_flags=pygame.BLEND_RGB_ADD
        )

    def paint(self) -> None:
        super().paint()
        if not self.enabled:
            self._paint_disabled()
        elif self.is_hovered:
            # pass
            self._paint_hovered()
        if self.use_effect and self.effect:
            self._paint_effect()

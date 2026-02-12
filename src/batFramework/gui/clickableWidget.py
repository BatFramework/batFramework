import batFramework as bf
from typing import Self, Callable, Any
from .interactiveWidget import InteractiveWidget
from .shape import Shape
import pygame


class ClickableWidget(Shape, InteractiveWidget):
    _cache: dict = {}

    def __init__(self, callback: Callable[[],Any] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.callback = callback
        self.is_pressed: bool = False # the state where the button is being held down (releasing will trigger callback)
        self.is_enabled: bool = True # 
        self.hover_cursor = bf.const.DEFAULT_HOVER_CURSOR
        self.click_cursor = bf.const.DEFAULT_CLICK_CURSOR

        self.click_down_sound = None
        self.click_up_sound = None
        self.get_focus_sound = None
        self.lose_focus_sound = None

        self.pressed_relief: int = 1    # Depth effect height when pressed
        self.unpressed_relief: int = 2  # Depth effect height when released (default)
        self.silent_focus: bool = False
        self.set_debug_color("cyan")
        self.set_relief(self.unpressed_relief)
        self.set_click_pass_through(False)

    def get_min_required_size(self) -> tuple[float, float]:
        res = super().get_min_required_size()
        res = res[0],res[1]+self.unpressed_relief
        return res

    def set_unpressed_relief(self, relief: int) -> Self:
        if relief == self.unpressed_relief:
            return self
        self.unpressed_relief = relief
        self.dirty_shape = True
        if not self.is_pressed:
            self.set_relief(relief)
        return self

    def set_pressed_relief(self, relief: int) -> Self:
        if relief == self.pressed_relief:
            return self
        self.pressed_relief = relief
        self.dirty_shape = True
        if self.is_pressed:
            self.set_relief(relief)
        return self

    def set_silent_focus(self, value: bool) -> Self:
        self.silent_focus = value
        return self

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

    def get_surface_filter(self) -> pygame.Surface | None:
        size = int(self.rect.w), int(self.rect.h)
        surface_filter = ClickableWidget._cache.get((size, *self.border_radius), None)
        if surface_filter is None:
            # Create a mask from the original surface
            mask = pygame.mask.from_surface(self.surface, threshold=0)

            silhouette_surface = mask.to_surface(
                setcolor=(30, 30, 30), unsetcolor=(0, 0, 0)
            )

            ClickableWidget._cache[(size, *self.border_radius)] = silhouette_surface

            surface_filter = silhouette_surface

        return surface_filter

    def allow_focus_to_self(self) -> bool:
        return True

    def enable(self) -> Self:
        self.is_enabled = True
        self.dirty_surface = True
        return self

    def disable(self) -> Self:
        self.is_enabled = False
        self.dirty_surface = True
        return self

    def set_callback(self, callback: Callable[[],Any]) -> Self:
        self.callback = callback
        return self

    def on_get_focus(self):
        super().on_get_focus()
        if self.get_focus_sound and not self.silent_focus:
            if self.parent_scene and self.parent_scene.visible:
                bf.AudioManager().play_sound(self.get_focus_sound)
        if self.silent_focus:
            self.silent_focus = False

    def on_lose_focus(self):
        super().on_lose_focus()
        if self.lose_focus_sound and not self.silent_focus:
            if self.parent_scene and self.parent_scene.visible:
                bf.AudioManager().play_sound(self.lose_focus_sound)
        if self.silent_focus:
            self.silent_focus = False

    def __str__(self) -> str:
        return f"ClickableWidget"

    def click(self, force=False) -> None:
        if not self.is_enabled and not force:
            return False
        if self.callback is not None:
            self.callback()
            return True
        return False
 
    def on_key_down(self, key,event):
        if key == pygame.K_SPACE:
            self.on_click_down(1,event)
        self.do_on_key_down(key,event)
    
    def on_key_up(self, key,event):
        if key == pygame.K_SPACE:
            self.on_click_up(1,event)
        self.do_on_key_down(key,event)

    def on_click_down(self, button,event) -> None :
        if button < 1 or button > 5 :
            return
        self.is_clicked_down[button-1] = True
        if button != 1:
            return        
        event.consumed = not self.click_pass_through
        if self.is_enabled and self.get_focus():
            self.is_pressed = True
            if self.click_down_sound:
                bf.AudioManager().play_sound(self.click_down_sound)
            pygame.mouse.set_cursor(self.click_cursor)
            self.set_relief(self.pressed_relief)
            self.do_on_click_down(button,event)

    def on_click_up(self, button,event):
        if button < 1 or button > 5 :
            return
        self.is_clicked_down[button-1] = False
        if button != 1 :
            return
        event.consumed = not self.click_pass_through
        if self.is_enabled and self.is_pressed:
            self.is_pressed = False
            if self.click_up_sound:
                bf.AudioManager().play_sound(self.click_up_sound)
            self.set_relief(self.unpressed_relief)
            self.click()
            self.do_on_click_up(button,event)

    def on_enter(self) -> None:
        self.is_hovered = True
        if not self.is_enabled:
            return
        super().on_enter()
        self.dirty_surface = True
        pygame.mouse.set_cursor(self.hover_cursor)

    def on_exit(self) -> None:
        super().on_exit()
        if self.is_pressed:
            self.set_relief(self.unpressed_relief)
        self.is_pressed = False
        self.dirty_surface = True
        pygame.mouse.set_cursor(bf.const.DEFAULT_CURSOR)

    def on_lose_focus(self):
        super().on_lose_focus()
        self.on_exit()

    def _paint_disabled(self) -> None:
        self.surface.blit(
            self.get_surface_filter(), (0, 0), special_flags=pygame.BLEND_RGB_SUB
        )

    def _paint_hovered(self) -> None:
        self.surface.blit(
            self.get_surface_filter(), (0, 0), special_flags=pygame.BLEND_RGB_ADD
        )

    def get_inner_rect(self) -> pygame.FRect:
        return pygame.FRect(
            self.rect.x + self.padding[0],
            self.rect.y + self.padding[1] + (self.unpressed_relief - self.pressed_relief if self.is_pressed else 0),
            self.rect.w - self.padding[2] - self.padding[0],
            self.rect.h - self.unpressed_relief - self.padding[1] - self.padding[3],
        )

    def get_local_inner_rect(self) -> pygame.FRect:
        return pygame.FRect(
            self.padding[0],
            self.padding[1] + (self.unpressed_relief - self.pressed_relief if self.is_pressed else 0),
            self.rect.w - self.padding[2] - self.padding[0],
            self.rect.h - self.unpressed_relief - self.padding[1] - self.padding[3],
        )


    def _get_elevated_rect(self) -> pygame.FRect:
        return pygame.FRect(
            0,
            self.unpressed_relief - self.pressed_relief if self.is_pressed else 0,
            self.rect.w,
            self.rect.h - self.unpressed_relief,
        )

    def paint(self) -> None:
        super().paint()
        if not self.is_enabled:
            self._paint_disabled()
        elif self.is_hovered:
            self._paint_hovered()
 

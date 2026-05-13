import batFramework as bf
from typing import Self, Callable, Any
from .interactiveShape import InteractiveShape
import pygame


class ClickableWidget(InteractiveShape):
    _cache: dict = {}

    def __init__(self, callback: Callable[[], Any] = None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.callback = callback
        self.is_pressed: bool = False  # held down; releasing triggers the callback
        self.click_down_sound: str | None = None
        self.click_up_sound: str | None = None

        self.pressed_relief: int = 0    # depth effect height when pressed
        self.unpressed_relief: int = 0  # depth effect height when released

        self.set_debug_color("orange")
        self.set_relief(self.unpressed_relief)
        self.set_click_pass_through(False)

    # -------------------------------------------------------------------------
    # Size / relief
    # -------------------------------------------------------------------------

    def get_min_required_size(self) -> tuple[float, float]:
        res = super().get_min_required_size()
        return res[0], res[1] + self.unpressed_relief

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

    # -------------------------------------------------------------------------
    # Sound / callback setters
    # -------------------------------------------------------------------------

    def set_click_down_sound(self, sound_name: str) -> Self:
        self.click_down_sound = sound_name
        return self

    def set_click_up_sound(self, sound_name: str) -> Self:
        self.click_up_sound = sound_name
        return self

    def set_callback(self, callback: Callable[[], Any]) -> Self:
        self.callback = callback
        return self

    # -------------------------------------------------------------------------
    # Click logic
    # -------------------------------------------------------------------------

    def click(self, force: bool = False) -> bool:
        if not self.is_enabled and not force:
            return False
        if self.callback is not None:
            self.callback()
            return True
        return False

    def on_key_down(self, key, event):
        if key == pygame.K_SPACE:
            self.on_click_down(1, event)
        self.do_on_key_down(key, event)

    def on_key_up(self, key, event):
        if key == pygame.K_SPACE:
            self.on_click_up(1, event)
        self.do_on_key_up(key, event)

    def on_click_down(self, button, event) -> None:
        if button < 1 or button > 5:
            return
        self.is_clicked_down[button - 1] = True
        if button != 1:
            return
        if not self.click_pass_through:
            event.consumed = True
        if self.is_enabled and self.ask_focus():
            self.is_pressed = True
            if self.click_down_sound and not self._suppress_sounds:
                bf.AudioManager().play_sound(self.click_down_sound)
            pygame.mouse.set_cursor(self.click_cursor)
            self.set_relief(self.pressed_relief)
            self.do_on_click_down(button, event)

    def on_click_up(self, button, event) -> None:
        if button < 1 or button > 5:
            return
        self.is_clicked_down[button - 1] = False
        if button != 1:
            return
        if not self.click_pass_through:
            event.consumed = True
        if self.is_enabled and self.is_pressed:
            self.is_pressed = False
            if self.click_up_sound and not self._suppress_sounds:
                bf.AudioManager().play_sound(self.click_up_sound)
            self.set_relief(self.unpressed_relief)
            self.click()
            self.do_on_click_up(button, event)

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

    # -------------------------------------------------------------------------
    # Inner rect helpers (account for press offset)
    # -------------------------------------------------------------------------

    def get_inner_rect(self) -> pygame.FRect:
        return pygame.FRect(
            self.rect.x + self.padding[0],
            self.rect.y
            + self.padding[1]
            + (self.unpressed_relief - self.pressed_relief if self.is_pressed else 0),
            self.rect.w - self.padding[2] - self.padding[0],
            self.rect.h - self.unpressed_relief - self.padding[1] - self.padding[3],
        )

    def get_local_inner_rect(self) -> pygame.FRect:
        return pygame.FRect(
            self.padding[0],
            self.padding[1]
            + (self.unpressed_relief - self.pressed_relief if self.is_pressed else 0),
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

    def __str__(self) -> str:
        return "ClickableWidget"
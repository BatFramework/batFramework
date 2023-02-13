import pygame

from . import lib as lib
from .interactive_entity import InteractiveEntity
from .label import Label


class Button(InteractiveEntity, Label):
    def __init__(self, text="") -> None:
        InteractiveEntity.__init__(self)
        Label.__init__(self,text)
        self._callback = None
        self._args = None
        self._mouse_in = False

    def set_callback(self, func, *args):
        self._callback = func
        self._args = args

    def trigger(self, parent=None):
        if self._callback:
            self._callback(*self._args)

    def on_key_down(self, key):
        if key == pygame.K_RETURN:
            if self.has_focus():
                self.trigger()

    def on_event(self, event: pygame.event.Event) -> bool:
        if not self.is_visible():return
        if event.type == pygame.MOUSEMOTION:
            rect = self.rect.copy()
            if not self.is_hud():
                rect.topleft = self.get_scene_link().get_screen_coordinates(*self.rect.topleft)
            if rect.collidepoint(pygame.mouse.get_pos()):
                self._mouse_in = True
            else:
                self._mouse_in = False

        elif event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]:
            if self._mouse_in:
                if self._parentContainer.has_focus():
                    self.get_focus()
                    self.trigger()
                    return True

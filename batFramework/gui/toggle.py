import batFramework as bf
import pygame
from .button import Button


class Toggle(Button):
    def __init__(self, text, callback=None, default_value=False):
        self.value = default_value
        self.deactivate_color = bf.color.DARK_RED
        self.activate_color = bf.color.GREEN
        super().__init__(text)
        self.set_callback(callback)

    def set_deactivate_color(self, color):
        self.deactivate_color = color
        self.update_surface()

    def set_activate_color(self, color):
        self.activate_color = color
        self.update_surface()

    def update(self, dt: float):
        if self.activate_container.is_active("key"):
            self.activate()
        elif self.rect.collidepoint(pygame.mouse.get_pos()):
            if self.activate_container.is_active("mouse"):
                self.activate(bypass_focus=True)
            else:
                self._hovering = True
        else:
            self._hovering = False
        self.activate_container.reset()
        if self._activate_flash > 0:
            self._activate_flash -= 60 * dt
            if self._activate_flash < 0:
                if self._callback:
                    self.toggle()
                    self._callback(self.value)
                if self.parent_container:
                    self.parent_container.lock_focus = False

    def toggle(self, value=None):
        if value != None:
            self.value = value
            if self._callback:
                self._callback(self.value)
        else:
            self.value = not self.value
        self.update_surface()


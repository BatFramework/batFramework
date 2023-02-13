import pygame

from batFramework import constants as c
from batFramework import lib as lib
from batFramework.color import Color
from batFramework.entitiy import Entity


class Label(Entity):
    def __init__(self, text="") -> None:
        super().__init__()
        self._text = None
        self._padding = c.DEFAULT_PADDING
        self._borderRadius = -1
        self._textColor = Color.WHITE
        self._backgroundColor = Color.TRANSPARENT
        self.set_text(text)


    def set_size(self, width, height):
        if super().set_size(width,height):
            self.set_auto_resize(False)
            self.update_dimensions()
            self.update_image()

    def set_position(self, x, y):
        super().set_position(x, y)

    def has_border_radius(self)-> bool:
        if isinstance(self._borderRadius,int):
            return self._borderRadius not in [-1,0] 
        if isinstance(self._borderRadius,list):
            return any([val not in [-1,0] for val in self._borderRadius])
        return False
    
    def set_border_radius(self, value):
        self._borderRadius = value
        self.update_image()

    def set_padding(self, x: int, y: int):
        if x < 0 or y < 0:
            return
        self._padding = [x, y]
        self.update_image()

    def set_text(self, newText: str):
        if newText == self.get_text():
            return
        self._text = newText
        self.update_dimensions()
        self.update_image()

    def get_text(self):
        return self._text

    def set_text_color(self, color):
        self._textColor = color
        self.update_image()

    def get_text_color(self):
        return self._textColor

    def set_background_color(self, color):
        self._backgroundColor = color
        self.update_image()

    def get_background_color(self):
        return self._backgroundColor

    def get_required_size(self)-> tuple[int]:
        size = lib.BASE_FONT.size(self.get_text())
        rect = pygame.Rect(0,0,*size)
        rect.inflate_ip(*self._padding)
        return rect.size

    def update_dimensions(self):
        if  self.has_auto_resize():

            required_size = self.get_required_size()
            if self.rect.size == required_size:
                return
            self.rect.size = required_size
            self.set_position(*self.get_position())
        self.image = pygame.Surface(self.rect.size).convert_alpha()


    def update_image(self):
        self.image.fill(Color.TRANSPARENT)

        bgColor = None if self._backgroundColor == Color.TRANSPARENT else self._backgroundColor
        text_surf = lib.BASE_FONT.render(
            self._text,
            c.FONT_ANTIALIASING,
            self._textColor,
            bgColor,
        ).convert_alpha()
        text_rect = text_surf.get_rect()
        tmp = self.rect.copy()
        tmp.topleft = (0,0)
        text_rect.center = tmp.center


        if self.has_border_radius():
            pygame.draw.rect(
                self.image, self._backgroundColor, self.rect, 0, self._borderRadius
            )
        else:
            self.image.fill(self._backgroundColor)

        self.image.blit(text_surf, text_rect)

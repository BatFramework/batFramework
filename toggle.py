import pygame

from batFramework import Color
from batFramework import constants as c
from batFramework import lib as lib
from batFramework.button import Button


class Toggle(Button):
    def __init__(
        self, text="", defaultValue=True) -> None:
        self._indicatorRect = pygame.Rect(0, 0, 16, 16)
        self._indicatorBorderRadius = 0
        self._indicatorGap = 10
        self._value: bool = defaultValue
        super().__init__(text)
        self.set_padding(*c.DEFAULT_PADDING)

    def set_indicator_size(self, width, height):
        self._indicatorRect.width = width
        self._indicatorRect.height = height

    def set_indicator_border_radius(self, value: int):
        self._indicatorBorderRadius = value

    def set_indicator_gap(self, value: int):
        self._indicatorGap = value

    def trigger(self, parent=None):
        self._value = not self._value
        self.update_image()
        if self._callback:
            self._callback(self._value)

    def get_value(self) -> bool:
        return self._value

    def get_required_size(self) -> tuple[int]:
        size = lib.BASE_FONT.size(self.get_text())
        size = (size[0]+self._indicatorRect.width + self._indicatorGap,size[1])
        rect = pygame.Rect(0,0,*size)
        rect.inflate_ip(*self._padding)
        return rect.size
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
        textAndIndicatorRect = text_rect.copy()
        textAndIndicatorRect.width += self._indicatorRect.width + self._indicatorGap

        tmp = self.rect.copy()
        tmp.topleft = (0,0)
        textAndIndicatorRect.center = tmp.center
        self._indicatorRect.midright = textAndIndicatorRect.midright
        text_rect.midleft = textAndIndicatorRect.midleft

        if self.has_border_radius():
            pygame.draw.rect(
                self.image, self._backgroundColor, self.rect, 0, self._borderRadius
            )
        else:
            self.image.fill(self._backgroundColor)
            

        self.image.blit(text_surf, text_rect)


        pygame.draw.rect(
            self.image,
            Color.GREEN if self.get_value() else Color.RED,
            self._indicatorRect,
            0,
        )
        pygame.draw.rect(self.image, Color.WHITE, self._indicatorRect, 2)

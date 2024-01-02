import batFramework as bf
from .widget import Widget
import pygame


class Shape(Widget):
    def __init__(self, width: float, height: float):
        self._color = (0, 0, 0, 0)
        self._border_radius: list[int] = [0]
        self._outline: int = 0
        self._outline_color: tuple[int, int, int] | str = (0, 0, 0, 0)
        super().__init__(convert_alpha=True)
        self.set_size(width, height)

    def to_string_id(self) -> str:
        return "Shape"

    def set_color(self, color: tuple[int, int, int] | str) -> "Frame":
        self._color = color
        self.build()
        return self

    def set_outline_color(self, color: tuple[int, int, int] | str) -> "Frame":
        self._outline_color = color
        self.build()
        return self

    def set_border_radius(self, value: int | list[int]) -> "Frame":
        if isinstance(value, int):
            self._border_radius = [value]
        else:
            self._border_radius = value
        self.build()
        return self

    def set_outline_width(self, value: int) -> "Frame":
        self._outline = value
        self.build()
        return self

    def build(self) -> None:
        if self.surface.get_size() != self.get_size_int():
            self.surface = pygame.Surface(self.get_size_int())
            if self.convert_alpha:
                self.surface = self.surface.convert_alpha()
                self.surface.fill((0, 0, 0, 0))
            if self.parent:
                self.parent.children_modified()
        if self._border_radius == [0]:
            self._build_shape()
            if self._outline:
                self._build_outline()
        else:
            self._build_rounded_shape()
            if self._outline:
                self._build_rounded_outline()

    def _build_shape(self) -> None:
        self.surface.fill(self._color)

    def _build_rounded_shape(self) -> None:
        self.surface.fill((0, 0, 0, 0))
        pygame.draw.rect(
            self.surface, self._color, (0, 0, *self.rect.size), 0, *self._border_radius
        )

    def _build_outline(self) -> None:
        pygame.draw.rect(
            self.surface, self._outline_color, (0, 0, *self.rect.size), self._outline
        )

    def _build_rounded_outline(self) -> None:
        pygame.draw.rect(
            self.surface,
            self._outline_color,
            (0, 0, *self.rect.size),
            self._outline,
            *self._border_radius,
        )

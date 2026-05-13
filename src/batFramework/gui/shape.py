from __future__ import annotations
import batFramework as bf
from .widget import Widget
import pygame
from typing import Self, Iterable
from math import ceil


class Shape(Widget):
    def __init__(self, size: tuple[float, float] | None = None, *args, **kwargs):
        super().__init__(size=size, convert_alpha=True)

        self.color = (0, 0, 0, 0)
        self.border_radius: list[int] = [0]
        self.outline_width: int = 0
        self.outline_color: pygame.typing.ColorLike = (0, 0, 0, 255)
        self.texture_surface = None
        self.texture_subsize = (0, 0)
        self.relief = 0
        self.shadow_color: pygame.typing.ColorLike = (0, 0, 0, 255)
        self.draw_mode = bf.drawMode.SOLID

    def get_inner_bottom(self) -> float:
        return self.rect.bottom - self.padding[3] - self.relief

    def get_inner_height(self) -> float:
        return self.rect.h - self.padding[1] - self.padding[3] - self.relief

    def get_inner_top(self) -> float:
        return self.rect.y + self.padding[1]

    def get_local_inner_rect(self) -> pygame.FRect:
        return pygame.FRect(
            self.padding[0],
            self.padding[1],
            self.rect.w - self.padding[2] - self.padding[0],
            self.rect.h - self.padding[1] - self.padding[3] - self.relief,
        )

    def get_inner_rect(self) -> pygame.FRect:
        return pygame.FRect(
            self.rect.x + self.padding[0],
            self.rect.y + self.padding[1],
            self.rect.w - self.padding[2] - self.padding[0],
            self.rect.h - self.padding[1] - self.padding[3] - self.relief,
        )

    def set_shadow_color(self, color: pygame.typing.ColorLike) -> Self:
        self.shadow_color = color
        self.dirty_surface = True
        return self

    def set_relief(self, relief: int) -> Self:
        if relief < 0:
            return self
        self.dirty_shape = self.relief != relief
        self.relief = relief
        return self

    def set_texture(
        self, surface: pygame.Surface, subsize: tuple[int, int] | None = None
    ) -> Self:
        self.texture_surface = surface
        if subsize is None:
            subsize = (ceil(surface.get_width() / 3), ceil(surface.get_height() / 3))
        self.texture_subsize = subsize
        self.dirty_surface = True
        return self

    def set_draw_mode(self, mode: bf.drawMode) -> Self:
        self.draw_mode = mode
        self.dirty_surface = True
        return self

    def get_draw_mode(self) -> bf.drawMode:
        return self.draw_mode

    def has_alpha_color(self) -> bool:
        return (pygame.Color(self.color).a != 255) or (
            pygame.Color(self.outline_color).a != 255
        )

    def __str__(self) -> str:
        return "Shape"

    def set_color(self, color: pygame.typing.ColorLike) -> Self:
        self.color = color
        self.dirty_surface = True
        return self

    def set_outline_color(self, color: pygame.typing.ColorLike) -> Self:
        self.outline_color = color
        self.dirty_surface = True
        return self

    def set_border_radius(self, value: int | list[int]) -> Self:
        if isinstance(value, int):
            self.border_radius = [value]
        else:
            self.border_radius = value
        self.dirty_surface = True
        return self

    def set_outline_width(self, value: int) -> Self:
        self.outline_width = value
        self.dirty_surface = True
        return self

    def paint(self) -> None:
        self._resize_surface()
        if self.draw_mode == bf.drawMode.TEXTURED:
            self._paint_textured()
            return
        if self.border_radius == [0]:
            self._paint_shape()
            if self.outline_width:
                self._paint_outline()
        else:
            self._paint_rounded_shape()
            if self.outline_width:
                self._paint_rounded_outline()


    def _paint_textured(self) -> None:
        self.surface.fill((0, 0, 0, 0))
        if self.texture_surface is None:
            return
        

        if self.relief != 0:
            elevated_rect = self._get_elevated_rect()
            base_rect     = self._get_base_rect()
            union =elevated_rect.union(base_rect)
            bf.utils.blit_9slice(self.texture_surface,self.texture_subsize,self.surface,union)
            if self.shadow_color is not None:
                shadow_overlay = pygame.Surface(
                    (int(union.w), int(union.h)), pygame.SRCALPHA
                )
                shadow_overlay.fill(self.shadow_color)
                self.surface.blit(
                    shadow_overlay,
                    union.topleft,
                    special_flags=pygame.BLEND_RGBA_MULT,
                )
            # --- Elevated (top face) region ---
            bf.utils.blit_9slice(self.texture_surface,self.texture_subsize,self.surface,elevated_rect)

        else:

            bf.utils.blit_9slice(self.texture_surface,self.texture_subsize,self.surface)

    def _get_elevated_rect(self) -> pygame.FRect:
        return pygame.FRect(0, 0, self.rect.w, self.rect.h - self.relief)

    def _get_base_rect(self) -> pygame.FRect:
        return pygame.FRect(0, self.rect.h - self.relief, self.rect.w, self.relief)

    def _paint_shape(self) -> None:
        self.surface.fill((0, 0, 0, 0))
        if self.relief != 0:
            if self.shadow_color is not None:
                self.surface.fill(self.shadow_color, self._get_base_rect())
            if self.color is not None:
                self.surface.fill(self.color, self._get_elevated_rect())

        elif self.color is not None:
            self.surface.fill(self.color, self._get_elevated_rect())

    def _paint_rounded_shape(self) -> None:
        self.surface.fill((0, 0, 0, 0))
        e = self._get_elevated_rect()
        if self.relief != 0:
            b = e.copy()
            b.bottom = self.rect.h
            if self.shadow_color is not None:
                pygame.draw.rect(
                    self.surface, self.shadow_color, b, 0, *self.border_radius
                )
            if self.color is not None:
                pygame.draw.rect(self.surface, self.color, e, 0, *self.border_radius)
        elif self.color is not None:
            pygame.draw.rect(self.surface, self.color, e, 0, *self.border_radius)

    def _paint_outline(self) -> None:
        if self.outline_color is None:
            return
        pygame.draw.rect(
            self.surface,
            self.outline_color,
            self._get_elevated_rect(),
            self.outline_width,
        )

    def build(self):
        target = self.resolve_size(self.get_min_required_size())
        changed = self.rect.size != target
        if changed:
            self.set_size(target)

        return changed

    def _paint_rounded_outline(self) -> None:
        if self.outline_color is None:
            return
        e = self._get_elevated_rect()
        b = e.copy()
        b.h += e.bottom - b.bottom

        pygame.draw.rect(
            self.surface,
            self.outline_color,
            e,
            self.outline_width,
            *self.border_radius,
        )
        if self.relief:
            pygame.draw.rect(
                self.surface,
                self.outline_color,
                b,
                self.outline_width,
                *self.border_radius,
            )
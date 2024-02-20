import batFramework as bf
from .widget import Widget
import pygame
from typing import Self
from math import ceil


class Shape(Widget):
    def __init__(self, width: float, height: float):
        self.color = (0, 0, 0, 0)
        self.border_radius: list[int] = [0]
        self.outline: int = 0
        self.outline_color: tuple[int, int, int] | str = (0, 0, 0, 0)
        self.texture_surface = None
        self.texture_subsize = (0,0)
        self.draw_mode = bf.drawMode.SOLID
        super().__init__(convert_alpha=True)
        self.set_size(width, height)

    def set_texture(self,surface:pygame.SurfaceType,subsize: tuple[int,int]|None=None)->Self:
        self.texture_surface = surface
        if subsize is None:
            subsize = (ceil(surface.get_width()/3),ceil(surface.get_height()/3))
        self.texture_subsize = subsize
        self.build()
        return self

    def set_draw_mode(self,mode:bf.drawMode)->Self:
        self.draw_mode = mode
        self.build()
        return self

    def has_alpha_color(self)->bool:
        return (pygame.Color(self.color).a != 255) or (pygame.Color(self.outline_color).a!=255)

    def to_string_id(self) -> str:
        return "Shape"

    def set_color(self, color: tuple[int, int, int] | str) -> Self:
        self.color = color
        self.build()
        return self

    def set_outline_color(self, color: tuple[int, int, int] | str) -> Self:
        self.outline_color = color
        self.build()
        return self

    def set_border_radius(self, value: int | list[int]) -> Self:
        if isinstance(value, int):
            self.border_radius = [value]
        else:
            self.border_radius = value
        self.build()
        return self

    def set_outline_width(self, value: int) -> Self:
        self.outline = value
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
        if self.draw_mode == bf.drawMode.TEXTURED:
            self._build_textured()
            return
        if self.border_radius == [0]:
            self._build_shape()
            if self.outline:
                self._build_outline()
        else:
            self._build_rounded_shape()
            if self.outline:
                self._build_rounded_outline()

    def _build_textured(self)->None:
        self.surface.fill((0,0,0,0))
        if self.texture_surface is None : return
        w,h = self.surface.get_size()
        sw,sh = self.texture_surface.get_size()
        sub = self.texture_subsize

        #center
        center_surface = self.texture_surface.subsurface((sub[0],sub[1],*sub)) 
        top_surface = self.texture_surface.subsurface((sub[0],0,*sub)) 
        bottom_surface = self.texture_surface.subsurface((sub[0], sh - sub[1], *sub))
        left_surface = self.texture_surface.subsurface((0, sub[1],*sub))
        right_surface = self.texture_surface.subsurface((sw - sub[0], sub[1],*sub))

        lst = []
        for y in range(sub[1],h+1-sub[1]*2,sub[1]):
            for x in range(sub[0],w+1-sub[0]*2,sub[0]):
                lst.append((center_surface,(x,y)))
        
        w_remainder = h_remainder = 0
        fix_x = fix_y = 0

        if w > sub[0]:
            fix_x = ((w//sub[0])-1)*sub[0]
            w_remainder = w % sub[0]
            # Center : Fix holes on the x axis
            if (w_remainder > 0):
                h_portion = center_surface.subsurface(0, 0, w_remainder, sub[1])
                for y in range(sub[1], h - sub[1]*2, sub[1]):
                    lst.append((h_portion,  (fix_x,y)))

            # Fix partial holes on the top
            if (w_remainder> 0):
                t_portion = top_surface.subsurface(0, 0, w_remainder, sub[1])
                lst.append((t_portion, (fix_x, 0)))

            # Fix partial holes on the bottom
            if (w_remainder> 0):
                b_portion = bottom_surface.subsurface(0, 0, w_remainder, sub[1])
                lst.append((b_portion, (fix_x, h - sub[1]-1)))

        if h > sub[1]:
            fix_y = ((h//sub[1])-1)*sub[1]
            h_remainder = h % sub[1]
            # Center : Fix holes on the y axis
            if (v_remainder := h % sub[1]) > 0:
                v_portion = center_surface.subsurface(0, 0, sub[0], v_remainder)
                for x in range(sub[0], w - sub[0]*2, sub[0]):
                    lst.append((v_portion, (x, fix_y)))

            # Fix partial holes on the left
            if (h_remainder>0):
                l_portion = left_surface.subsurface(0, 0, sub[0], h_remainder)
                lst.append((l_portion, (0, fix_y)))

            # Fix partial holes on the right
            if (h_remainder>0):
                r_portion = right_surface.subsurface(0, 0, sub[0], h_remainder)
                lst.append((r_portion, (w - sub[0]-1,fix_y)))

        if h > sub[1] or w > sub[0]:
            corner_portion = center_surface.subsurface(0,0,w_remainder if w_remainder else sub[0],h_remainder if h_remainder else sub[1])
            if w_remainder == 0: fix_x -= sub[0] 
            if h_remainder == 0: fix_y -= sub[1] 
            lst.append((corner_portion,(fix_x-1,fix_y-1)))

        self.surface.fblits(lst)
        
        # top
        self.surface.fblits([(top_surface,(x,0)) for x in range(sub[0],w+1-sub[0]*2,sub[0])])

        # bottom
        self.surface.fblits([(bottom_surface, (x, h - sub[1]-1)) for x in range(sub[0], w+1-sub[0]*2, sub[0])])

        # left
        self.surface.fblits([(left_surface, (0, y)) for y in range(sub[1], h+1-sub[1]*2 , sub[1])])

        # right
        self.surface.fblits([(right_surface, (w - sub[0]-1, y)) for y in range(sub[1], h+1-sub[1]*2 , sub[1])])

        # corners
        self.surface.fblits([
            (self.texture_surface.subsurface((0,0,*sub)),(0,0)),
            (self.texture_surface.subsurface((sw-sub[0],0,*sub)),(w-sub[0]-1,0)),
            (self.texture_surface.subsurface((0,sh-sub[1],*sub)),(0,h-sub[1]-1)),
            (self.texture_surface.subsurface((sw-sub[0],sh-sub[1],*sub)),(w-sub[0]-1,h-sub[1]-1)),
        ])

    def _build_shape(self) -> None:
        self.surface.fill(self.color)

    def _build_rounded_shape(self) -> None:
        self.surface.fill((0, 0, 0, 0))
        pygame.draw.rect(
            self.surface, self.color, (0, 0, *self.rect.size), 0, *self.border_radius
        )

    def _build_outline(self) -> None:
        pygame.draw.rect(
            self.surface, self.outline_color, (0, 0, *self.rect.size), self.outline
        )

    def _build_rounded_outline(self) -> None:
        pygame.draw.rect(
            self.surface,
            self.outline_color,
            (0, 0, *self.rect.size),
            self.outline,
            *self.border_radius,
        )

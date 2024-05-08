import batFramework as bf
from .widget import Widget
import pygame
from typing import Self
from math import ceil


class Shape(Widget):
    def __init__(self, size : tuple[float,float]):
        self.color = (0, 0, 0, 0)
        self.border_radius: list[int] = [0]
        self.outline: int = 0
        self.outline_color: tuple[int, int, int] | str = (0, 0, 0, 0)
        self.texture_surface = None
        self.texture_subsize = (0,0)
        self.relief = 0
        self.shadow_color : tuple[int, int, int] | str = (0, 0, 0, 255)
        self.draw_mode = bf.drawMode.SOLID
        super().__init__(convert_alpha=True)
        self.set_size(size)

    def get_padded_bottom(self) -> float:
        return self.rect.bottom - self.padding[3] - self.relief

    def get_padded_height(self) -> float:
        return self.rect.h - self.padding[1] - self.padding[3] - self.relief

    def set_shadow_color(self,color : tuple[int, int, int] | str )->Self:
        self.shadow_color = color
        self.build()
        return self

    def set_relief(self,relief:int)->Self:
        if relief < 0 : return self
        self.relief = relief
        self.build()
        return self

    def get_relief(self)->int:
        return self.relief

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

    def get_draw_mode(self)->bf.drawMode:
        return self.draw_mode

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
        target_size = self.get_size_int()
        if self.surface.get_size() != target_size:
            self.surface = pygame.Surface(target_size)
            if self.convert_alpha:
                self.surface = self.surface.convert_alpha()
                self.surface.fill((0, 0, 0, 0))
            if self.parent: # changed size, notify parent
                self.parent.notify()
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

    def _get_elevated_rect(self)->pygame.Rect:
        return pygame.FRect(0,self.relief - self.get_relief(), self.rect.w, self.rect.h-self.relief)
    
    def _get_base_rect(self)->pygame.Rect:
        return pygame.FRect(0,self.rect.h - self.get_relief(), self.rect.w, self.get_relief())

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
        
        w_remainder = w % sub[0]
        h_remainder = h % sub[1]
        fix_x = ((w//sub[0])-1)*sub[0]
        fix_y = ((h//sub[1])-1)*sub[1]

        if (w > sub[0]) and (w_remainder > 0):
        
            # Center : Fix gaps on the x axis
            h_portion = center_surface.subsurface(0, 0, w_remainder, sub[1])
            for y in range(sub[1], h - sub[1]*2, sub[1]):
                lst.append((h_portion,  (fix_x,y)))

            # Fix partial gaps on the top
            
            t_portion = top_surface.subsurface(0, 0, w_remainder, sub[1])
            lst.append((t_portion, (fix_x, 0)))

            # Fix partial gaps on the bottom
            b_portion = bottom_surface.subsurface(0, 0, w_remainder, sub[1])
            lst.append((b_portion, (fix_x, h - sub[1]-1)))

        if (h > sub[1]) and (h_remainder > 0):
            # Center : Fix gaps on the y axis
            v_portion = center_surface.subsurface(0, 0, sub[0], h_remainder)
            for x in range(sub[0], w - sub[0]*2, sub[0]):
                lst.append((v_portion, (x, fix_y)))

            # Fix partial gaps on the left
            l_portion = left_surface.subsurface(0, 0, sub[0], h_remainder)
            lst.append((l_portion, (0, fix_y)))

            # Fix partial gaps on the right
            r_portion = right_surface.subsurface(0, 0, sub[0], h_remainder)
            lst.append((r_portion, (w - sub[0]-1,fix_y)))

        # fix corner gap
        if h > sub[1] or w > sub[0]:
            corner_portion = center_surface.subsurface(0,0,w_remainder if w_remainder else sub[0],h_remainder if h_remainder else sub[1])
            if w_remainder == 0: fix_x -= sub[0] 
            if h_remainder == 0: fix_y -= sub[1] 
            lst.append((corner_portion,(fix_x-1,fix_y-1)))

        
        # borders
        lst.extend(
            [(top_surface,(x,0)) for x in range(sub[0],w+1-sub[0]*2,sub[0])] +
            [(bottom_surface, (x, h - sub[1]-1)) for x in range(sub[0], w+1-sub[0]*2, sub[0])] +
            [(left_surface, (0, y)) for y in range(sub[1], h+1-sub[1]*2 , sub[1])] + 
            [(right_surface, (w - sub[0]-1, y)) for y in range(sub[1], h+1-sub[1]*2 , sub[1])]+
            [
                (self.texture_surface.subsurface((0,0,*sub)),(0,0)),
                (self.texture_surface.subsurface((sw-sub[0],0,*sub)),(w-sub[0]-1,0)),
                (self.texture_surface.subsurface((0,sh-sub[1],*sub)),(0,h-sub[1]-1)),
                (self.texture_surface.subsurface((sw-sub[0],sh-sub[1],*sub)),(w-sub[0]-1,h-sub[1]-1)),
            ])
        
        self.surface.fblits(lst)

    def _build_shape(self) -> None:
        self.surface.fill((0,0,0,0))
        self.surface.fill(self.shadow_color,self._get_base_rect())
        self.surface.fill(self.color,self._get_elevated_rect())

    def _build_rounded_shape(self) -> None:
        self.surface.fill((0, 0, 0, 0))
        r = self._get_elevated_rect()
        r.bottom = self.rect.h        
        pygame.draw.rect(
            self.surface, self.shadow_color, r, 0, *self.border_radius
        )
        
        pygame.draw.rect(
            self.surface, self.color, self._get_elevated_rect(), 0, *self.border_radius
        )

    def _build_outline(self) -> None:
        if self.relief : pygame.draw.rect(
            self.surface, self.outline_color, (0,self.relief - self.get_relief(),self.rect.w,self.rect.h-self.relief), self.outline
        )
        pygame.draw.rect(
            self.surface, self.outline_color, (0,self.relief - self.get_relief(),self.rect.w,self.rect.h-(self.relief - self.get_relief())), self.outline
        )

    def _build_rounded_outline(self) -> None:
        pygame.draw.rect(
            self.surface,
            self.outline_color,
            self._get_elevated_rect().move(0,self.relief),
            self.outline,
            *self.border_radius,
        )
        if self.relief : 
            pygame.draw.rect(
            self.surface,
            self.outline_color,
            self._get_elevated_rect(),
            self.outline,
            *self.border_radius,
            )
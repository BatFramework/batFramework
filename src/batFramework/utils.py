import pygame
from enum import Enum
import os
import batFramework as bf
import json
from .enums import *
import re
from typing import Callable, TYPE_CHECKING, Any
from functools import cache
if TYPE_CHECKING:
    from .object import Object
    from .entity import Entity


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Utils:

    @staticmethod
    def split_surface(
        surface: pygame.Surface, split_size: tuple[int, int], func=None
    ) -> dict[tuple[int, int], pygame.Surface]:
        """
        Splits a surface into subsurfaces and returns a dictionnary of them
        with their tuple coordinates as keys.
        Exemple : '(0,0) : Surface'
        """
        width, height = surface.get_size()
        res = {}
        for iy, y in enumerate(range(0, height, split_size[1])):
            for ix, x in enumerate(range(0, width, split_size[0])):
                sub = surface.subsurface((x, y, split_size[0], split_size[1]))

                if func is not None:
                    sub = func(sub)

                res[(ix, iy)] = sub

        return res

    @staticmethod
    def filter_text(text_mode: textMode):
        if text_mode == textMode.ALPHABETICAL:
            pattern = re.compile(r"[^a-zA-Z]")
        elif text_mode == textMode.NUMERICAL:
            pattern = re.compile(r"[^0-9]")
        elif text_mode == textMode.ALPHANUMERICAL:
            pattern = re.compile(r"[^a-zA-Z0-9]")
        else:
            raise ValueError("Unsupported text mode")

        def filter_function(s: str) -> str:
            return pattern.sub("", s)

        return filter_function


    @staticmethod
    @cache
    def create_spotlight(inside_color, outside_color, radius, radius_stop=None, dest_surf=None,size=None):
        """
        Draws a circle spotlight centered on a surface
        inner color on the center
        gradient towards outside color from radius to radius stop
        surface background is made transparent
        if des_surf is None:
            if size is None :  size is radius_stop*radius_stop
            returns the newly created surface of size 'size' with the spotlight drawn

        """
        if radius_stop is None:
            radius_stop = radius
        diameter = radius_stop * 2

        if dest_surf is None:
            if size is None:
                size = (diameter,diameter)
            dest_surf = pygame.Surface(size, pygame.SRCALPHA)
        
        dest_surf.fill((0,0,0,0))


        center = dest_surf.get_rect().center

        if radius_stop != radius:
            for r in range(radius_stop, radius - 1, -1):
                color = [
                    inside_color[i] + (outside_color[i] - inside_color[i]) * (r - radius) / (radius_stop - radius)
                    for i in range(3)
                ] + [255]  # Preserve the alpha channel as fully opaque
                pygame.draw.circle(dest_surf, color, center, r)
        else:
            pygame.draw.circle(dest_surf, inside_color, center, radius)

        return dest_surf

    @staticmethod
    def draw_spotlight(dest_surf:pygame.Surface,inside_color,outside_color,radius,radius_stop=None,center=None):
        if radius_stop is None:
            radius_stop = radius
        center = dest_surf.get_rect().center if center is None else center
        if radius_stop != radius:
            for r in range(radius_stop, radius - 1, -1):
                color = [
                    inside_color[i] + (outside_color[i] - inside_color[i]) * (r - radius) / (radius_stop - radius)
                    for i in range(3)
                ] + [255]
                pygame.draw.circle(dest_surf, color, center, r)
        else:
            pygame.draw.circle(dest_surf, inside_color, center, radius)

    @staticmethod
    def animate_move(entity:"Object", start_pos : tuple[float,float], end_pos:tuple[float,float])->Callable[[float],None]:
        def func(x):
            entity.set_center(start_pos[0]+(end_pos[0]-start_pos[0])*x,start_pos[1]+(end_pos[1]-start_pos[1])*x)
        return func
    
    def animate_move_to(entity: "Object", end_pos: tuple[float, float]) -> Callable[[float], None]:
        # Start position will be captured once when the animation starts
        start_pos = [None]

        def update_position(progression: float):
            if start_pos[0] is None:
                start_pos[0] = entity.rect.center  # Capture the start position at the start of the animation

            # Calculate new position based on progression
            new_x = start_pos[0][0] + (end_pos[0] - start_pos[0][0]) * progression
            new_y = start_pos[0][1] + (end_pos[1] - start_pos[0][1]) * progression

            # Set the entity's new position
            entity.set_center(new_x, new_y)

        return update_position

    @staticmethod
    def animate_alpha(entity:"Entity", start : int, end:int)->Callable[[float],None]:
        def func(x):
            entity.set_alpha(int(pygame.math.clamp(start+(end-start)*x,0,255)))
        return func
    



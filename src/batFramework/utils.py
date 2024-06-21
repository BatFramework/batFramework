import pygame
from enum import Enum
import os
import batFramework as bf
import json
from .enums import *
import re
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Utils:

    @staticmethod
    def split_surface(
        surface : pygame.Surface, split_size: tuple[int, int], func=None
    ) -> dict[tuple[int, int], pygame.Surface]:
        """
        Splits a surface into subsurfaces and returns a dictionnary of them
        with their tuple coordinates as keys.
        Exemple : '(0,0) : Surface' 
        """
        if surface is None:
            return None
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
            pattern = re.compile(r'[^a-zA-Z]')
        elif text_mode == textMode.NUMERICAL:
            pattern = re.compile(r'[^0-9]')
        elif text_mode == textMode.ALPHANUMERICAL:
            pattern = re.compile(r'[^a-zA-Z0-9]')
        else:
            raise ValueError("Unsupported text mode")
        
        def filter_function(s: str) -> str:
            return pattern.sub('', s)
        
        return filter_function
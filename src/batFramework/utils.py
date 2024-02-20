import pygame
from enum import Enum
import os
import batFramework as bf
import json

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Utils:
    @staticmethod
    def split_surface(surface,split_size:tuple[int,int],func=None) -> dict[tuple[int,int],pygame.Surface]:
        if surface is None : return None
        width, height = surface.get_size()
        res = {}
        for iy,y in enumerate(range(0, height, split_size[1])):
            for ix,x in enumerate(range(0, width, split_size[0])):
                sub = surface.subsurface((x, y, split_size[0], split_size[1]))

                if func is not None: sub = func(sub)
                
                res[(ix,iy)]=sub
                
        return res
        

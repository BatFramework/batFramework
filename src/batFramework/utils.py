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
    def img_slice(file, cell_width, cell_height, flipX=False,convert_alpha=True) -> list[pygame.Surface]:
        src = bf.ResourceManager().get_image(file,convert_alpha=convert_alpha)
        if src is None : exit(1)
        width, height = src.get_size()
        res = []
        for y in range(0, height, cell_height):
            for x in range(0, width, cell_width):
                sub = src.subsurface((x, y, cell_width, cell_height))
                if flipX:
                    sub = pygame.transform.flip(sub, True, False)

                res.append(sub)
        return res


def move_points(delta, *points):
    res = []
    for point in points:
        res.append((point[0] + delta[0], point[1] + delta[1]))
    return res

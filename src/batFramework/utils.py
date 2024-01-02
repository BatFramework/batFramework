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
    def load_json_from_file(path: str) -> dict|None:
        try:
            with open(Utils.get_path(path), "r") as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            print(f"File '{path}' not found")
            return None

    @staticmethod
    def save_json_to_file(path: str, data) -> bool:
        try:
            with open(Utils.get_path(path), "w") as file:
                json.dump(data, file, indent=2)
            return True
        except FileNotFoundError:
            return False


    @staticmethod
    def img_slice(file, cell_width, cell_height, flipX=False) -> list[pygame.Surface]:
        src = pygame.image.load(
            os.path.join(bf.const.RESOURCE_PATH, file)
        ).convert_alpha()
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

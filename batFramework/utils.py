import pygame
from enum import Enum
import os
import batFramework as bf
import json

FONT_FILENAME = "slkscr"


def move_points(delta, *points):
    res = []
    for point in points:
        res.append((point[0] + delta[0], point[1] + delta[1]))
    return res


class Direction(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class Alignment(Enum):
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    TOP = "top"
    BOTTOM = "bottom"


class Layout(Enum):
    FILL = "fill"
    FIT = "fit"


class Utils:
    pygame.font.init()

    FONTS: dict[int, pygame.Font] = {}
    for size in range(8, 50, 2):
        FONTS[size] = pygame.font.Font(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), f"fonts/{FONT_FILENAME}.ttf"
            ),
            size=size,
        )
        # FONTS[size].align = pygame.FONT_LEFT
        # FONTS[size].italic = True
        # FONTS[size].underline= True
        # FONTS[size].set_direction(pygame.DIRECTION_TTB)

    tilesets = {}

    class Tileset:
        _flip_cache = {}  # {"tileset":tileset,"index","flipX","flipY"}

        def __init__(self, surface: pygame.Surface, tilesize) -> None:
            self.tile_dict = {}
            self.surface = surface
            self.tile_size = tilesize
            self.split_surface(surface)

        def split_surface(self, surface: pygame.Surface):
            width, height = surface.get_size()
            num_tiles_x = width // self.tile_size
            num_tiles_y = height // self.tile_size
            # Iterate over the tiles vertically and horizontally
            for y in range(num_tiles_y):
                for x in range(num_tiles_x):
                    # Calculate the coordinates of the current tile in the tileset
                    tile_x = x * self.tile_size
                    tile_y = y * self.tile_size
                    # Create a subsurface for the current tile
                    tile_surface = surface.subsurface(
                        pygame.Rect(tile_x, tile_y, self.tile_size, self.tile_size)
                    )
                    # Calculate the unique key for the tile (e.g., based on its coordinates)
                    tile_key = (x, y)
                    # Store the subsurface in the dictionary with the corresponding key
                    self.tile_dict[tile_key] = tile_surface
            # print(self.tile_dict)

        def get_tile(self, x, y, flipX=False, flipY=False) -> pygame.Surface | None:
            if (x, y) not in self.tile_dict:
                return None
            if flipX or flipY:
                key = f"{x}{y}:{flipX}{flipY}"
                if not key in self._flip_cache:
                    self._flip_cache[key] = pygame.transform.flip(
                        self.tile_dict[(x, y)], flipX, flipY
                    )
                return self._flip_cache[key]
            return self.tile_dict[(x, y)]

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

    def load_tileset(path: str, name: str, tilesize):
        if name in Utils.tilesets:
            return Utils.tilesets[name]
        else:
            img = pygame.image.load(
                os.path.join(bf.const.RESOURCE_PATH, path)
            ).convert_alpha()
            tileset = Utils.Tileset(img, tilesize)
            Utils.tilesets[name] = tileset
            return tileset

    @staticmethod
    def get_tileset(name: str) -> Tileset:
        if name not in Utils.tilesets:
            return None
        return Utils.tilesets[name]

    @staticmethod
    def get_path(path: str):
        return os.path.join(bf.const.RESOURCE_PATH, path)

    @staticmethod
    def load_json_from_file(path: str) -> dict:
        try:
            with open(Utils.get_path(path), "r") as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            return None

    @staticmethod
    def save_json_to_file(path: str, data):
        try:
            with open(Utils.get_path(path), "w") as file:
                json.dump(data, file, indent=2)
            return True
        except FileNotFoundError:
            return False


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

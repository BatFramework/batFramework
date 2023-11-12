import pygame
from enum import Enum
import os
import batFramework as bf
import json

MAX_FONT_SIZE = 100
MIN_FONT_SIZE = 8

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


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
    FONTS = {}
    tilesets = {}

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
    def init_font(raw_path:str):
            try :
                if raw_path is not None:
                    Utils.load_font(raw_path if raw_path else None,None)
                Utils.load_font(raw_path)
            except FileNotFoundError:
                Utils.load_sysfont(raw_path)
                Utils.load_sysfont(raw_path,None)


    @staticmethod
    def load_font(path:str,name:str=''):
        if path is not None: path = Utils.get_path(path) # convert path if given
        filename = os.path.basename(path).split('.')[0] if path is not None else None # get filename if path is given, else None
        if name != '' : filename = name # if name is not given, name is the filename
        Utils.FONTS[filename] = {}
        # fill the dict 
        for size in range(MIN_FONT_SIZE, MAX_FONT_SIZE, 2):
            Utils.FONTS[filename][size] = pygame.font.Font(path,size=size)

    def load_sysfont(font_name:str,key:str=''):
        if key == '' : key = font_name
        if pygame.font.match_font(font_name) is None: 
            raise FileNotFoundError(f"Requested font '{font_namey}' was not found")
        Utils.FONTS[font_name] = {}

        for size in range(MIN_FONT_SIZE, MAX_FONT_SIZE, 2):
            Utils.FONTS[key][size] = pygame.font.SysFont(font_name,size=size)  
              

    @staticmethod
    def get_font(name:str|None=None,text_size:int=12) -> pygame.Font:
        if not name in Utils.FONTS: return None
        if not text_size in Utils.FONTS[name]: return None
        return Utils.FONTS[name][text_size]

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


    


def move_points(delta, *points):
    res = []
    for point in points:
        res.append((point[0] + delta[0], point[1] + delta[1]))
    return res

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

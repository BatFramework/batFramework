import pygame
from enum import Enum
import sys, os


if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS'.
    application_path = sys._MEIPASS
else:
    application_path = os.getcwd()

class Constants:
    SCREEN = None
    RESOLUTION: tuple[int, int] = (1280,720)
    VSYNC = 0
    FLAGS: int = pygame.SCALED | pygame.RESIZABLE
    FPS: int = 60
    RESOURCE_PATH = "."
    
    @staticmethod
    def init_screen(resolution:tuple[int,int],flags:int= 0, vsync:int= 0):
        Constants.RESOLUTION = resolution
        Constants.FLAGS = flags
        Constants.VSYNC = vsync
        Constants.SCREEN = pygame.display.set_mode(Constants.RESOLUTION, Constants.FLAGS,vsync=Constants.VSYNC)
        print(f"Window : {resolution[0]}x{resolution[1]}px | flags:{flags.bit_count()}, vsync:{pygame.display.is_vsync()}")
    MUSIC_END_EVENT = pygame.event.custom_type()

    # ------------GUI SPECIFIC
    DEFAULT_TEXT_SIZE: int = 8

    GUI_SCALE: int = 1
    # ---------------------

    @staticmethod
    def set_resolution(resolution : tuple[int,int]):
        Constants.RESOLUTION = resolution

    @staticmethod
    def set_resource_path(path: str):
        print("set resource path :", path)
        Constants.RESOURCE_PATH = os.path.join(application_path,path)

    @staticmethod
    def set_fps_limit(value: int):
        Constants.FPS = value
        print("FPS limit to : ", value)

    @staticmethod
    def set_gui_scale(value: int):
        Constants.GUI_SCALE = value
        print("GUI_SCALE to : ", value)

    @staticmethod
    def set_default_text_size(size:int):
        Constants.DEFAULT_TEXT_SIZE = size

class Colors:
    LIGHT_CYAN = (179, 229, 252)
    WASHED_BLUE = (52, 73, 94)
    RIVER_BLUE = (52, 152, 219)
    DARK_INDIGO = (40, 53, 147)
    LIGHT_BLUE = (3, 169, 244)
    DEEP_BLUE = (41, 121, 255)
    DARK_BLUE = (44, 62, 80)
    GREEN = (67, 160, 71)
    DARK_GREEN = (39, 174, 96)
    BROWN = (109, 76, 65)
    DARK_RED = (192, 57, 43)
    ORANGE = (251, 140, 0)
    CLOUD_WHITE = (236, 240, 241)
    SILVER = (189, 195, 199)
    DARK_GRAY = (66, 66, 66)

    DARK_GB = (27, 42, 9)
    SHADE_GB = (14, 69, 11)
    BASE_GB = (73, 107, 34)
    LIGHT_GB = (154, 158, 63)

class Axis(Enum):
    HORIZONTAL  = 1
    VERTICAL    = 2

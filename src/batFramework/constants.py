import pygame
from enum import Enum
import sys, os


if getattr(sys, "frozen", False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app
    # path into variable _MEIPASS'.
    application_path = sys._MEIPASS
else:
    application_path = os.getcwd()

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



class Constants:
    SCREEN = None
    RESOLUTION: tuple[int, int] = (1280, 720)
    VSYNC = 0
    FLAGS: int = pygame.SCALED | pygame.RESIZABLE
    FPS: int = 60
    MUSIC_END_EVENT = pygame.event.custom_type()

    BF_INITIALIZED : bool = False
    @staticmethod
    def set_resolution(resolution: tuple[int, int]):
        Constants.RESOLUTION = resolution

    @staticmethod
    def set_fps_limit(value: int):
        Constants.FPS = value
        print("FPS limit to : ", value)


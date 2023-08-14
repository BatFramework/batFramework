import pygame


class Constants:
    MUSIC_END_EVENT = pygame.event.custom_type()

    RESOLUTION: tuple[int, int] = (160, 144)
    # RESOLUTION :tuple[int,int]= (320, 288)
    # RESOLUTION :tuple[int,int]= (640, 360)
    # RESOLUTION = (1280, 720)

    # VSYNC = 1
    VSYNC = 0

    FLAGS: int = pygame.SCALED #| pygame.RESIZABLE
    # FLAGS = 0

    SCREEN = pygame.display.set_mode(RESOLUTION, FLAGS, vsync=VSYNC, depth=8)

    FPS: int = 60
    # FPS :int = 0

    # ------------GUI SPECIFIC
    DEFAULT_TEXT_SIZE: int = 8
    # DEFAULT_TEXT_SIZE :int= 12
    GUI_SCALE: int = 1
    FONT_ANTIALIASING: bool = False
    # FONT_ANTIALIASING :bool= True

    # ---------------------
    RESOURCE_PATH = "."

    @staticmethod
    def set_resource_path(path: str):
        print("set resource path :", path)
        Constants.RESOURCE_PATH = path

    @staticmethod
    def set_fps_limit(value: int):
        Constants.FPS = value
        print("FPS limit to : ", value)

    @staticmethod
    def set_gui_scale(value: int):
        Constants.GUI_SCALE = value
        print("GUI_SCALE to : ", value)


class Colors:
    LIGHT_CYAN = (179, 229, 252)
    WET_BLUE = (52, 73, 94)
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

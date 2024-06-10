import pygame


class Constants:
    SCREEN: pygame.Surface = None
    RESOLUTION: tuple[int, int] = (1280, 720)
    VSYNC = 0
    FLAGS: int = pygame.SCALED | pygame.RESIZABLE
    FPS: int = 60
    MUSIC_END_EVENT = pygame.event.custom_type()

    DEFAULT_CURSOR = pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW)
    DEFAULT_HOVER_CURSOR = pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW)
    DEFAULT_CLICK_CURSOR = pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW)

    BF_INITIALIZED: bool = False

    @staticmethod
    def set_resolution(resolution: tuple[int, int]):
        Constants.RESOLUTION = resolution

    @staticmethod
    def set_default_cursor(cursor: pygame.Cursor):
        Constants.DEFAULT_CURSOR = cursor

    @staticmethod
    def set_default_hover_cursor(cursor: pygame.Cursor):
        Constants.DEFAULT_HOVER_CURSOR = cursor

    @staticmethod
    def set_default_click_cursor(cursor: pygame.Cursor):
        Constants.DEFAULT_CLICK_CURSOR = cursor

    @staticmethod
    def set_fps_limit(value: int):
        Constants.FPS = value
        print("FPS limit to : ", value)

import pygame
from enum import Enum
import sys, os

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


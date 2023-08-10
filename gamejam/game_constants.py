import pygame
class GameConstants:
    TILE_SIZE = 8
    CHUNK_SIZE = 8
    FRICTION = 0.4
    GRAVITY = 800
    STEP_ON_EVENT = pygame.event.custom_type()

    VOLUME_TABLE = {"OFF":0,"LOW":0.3,"MEDIUM":0.6,"HIGH":1}

    DEFAULT_MUSIC_VOLUME = 0.3
    DEFAULT_SFX_VOLUME = 0.3


    TAGS = [
        "collider",
        "bounce",
        "pKill",
        "AKill",
        "+switch",
        "wave",
        ]
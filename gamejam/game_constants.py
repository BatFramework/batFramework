import pygame


class GameConstants:
    RESOLUTION = (160,144)
    FLAGS = pygame.SCALED
    VSYNC = 0
    TILE_SIZE = 8
    CHUNK_SIZE = 8
    FRICTION = 0.4
    GRAVITY = 800
    STEP_ON_EVENT = pygame.event.custom_type()

    VOLUME_TABLE = {"OFF": 0, "LOW": 0.3, "MEDIUM": 0.6, "HIGH": 1}

    DEFAULT_MUSIC_VOLUME = 0.3
    DEFAULT_SFX_VOLUME = 0.3

    TAGS = [
        "collider",
        "bounce",
        "pKill",
        "AKill",
        "+switch",
        "wave",
        "one_way_up",
    ]
    # TAGS = [str(i) for i in range(1,41)]
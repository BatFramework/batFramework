from enum import Enum


class Color(tuple, Enum):
    TRANSPARENT = (0, 0, 0, 0)
    BLACK = (0, 0, 0)
    RED = (239, 83, 80)
    GREEN = (102, 187, 106)
    BLUE = (33, 150, 243)
    DARK_GRAY = (40,40,40)
    GRAY = (100,100,100)
    LIGHT_GRAY = (180, 180, 180)
    WHITE = (255, 255, 255)
    LAVENDER = (57, 73, 171)
    LAVENDER_DARK = (26, 35, 126)
    PURPLE_LIGHT = (179, 157, 219)
    PURPLE = (103, 58, 183)
    INDIGO = (48, 79, 254)

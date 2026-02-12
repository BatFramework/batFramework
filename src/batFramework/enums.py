from __future__ import annotations
from enum import Enum
import pygame

playerInput = [pygame.KEYDOWN,pygame.MOUSEBUTTONDOWN,pygame.KEYUP,pygame.MOUSEBUTTONUP]

class color:
    WHITE = pygame.Color(255, 255, 255)
    LIGHTER_GRAY = pygame.Color(236, 240, 241)
    LIGHT_GRAY = pygame.Color(189, 195, 199)
    DARK_GRAY = pygame.Color(66, 66, 66)
    DARKER_GRAY = pygame.Color(23, 23, 23)
    BLACK = pygame.Color(0, 0, 0)

    TURQUOISE = pygame.Color(26, 188, 156)
    TURQUOISE_SHADE = pygame.Color(22, 160, 133)

    GREEN = pygame.Color(46, 204, 113)
    GREEN_SHADE = pygame.Color(39, 174, 96)

    BLUE = pygame.Color(52, 152, 219)
    BLUE_SHADE = pygame.Color(41, 128, 185)

    PURPLE = pygame.Color(155, 89, 182)
    PURPLE_SHADE = pygame.Color(142, 68, 173)

    CHARCOAL = pygame.Color(52, 73, 94)
    CHARCOAL_SHADE = pygame.Color(44, 62, 80)

    GOLD = pygame.Color(241, 196, 15)
    GOLD_SHADE = pygame.Color(243, 156, 18)

    ORANGE = pygame.Color(230, 126, 34)
    ORANGE_SHADE = pygame.Color(211, 84, 0)

    RED = pygame.Color(231, 76, 60)
    RED_SHADE = pygame.Color(192, 57, 43)

    CLOUD = pygame.Color(236, 240, 241)
    CLOUD_SHADE = pygame.Color(189, 195, 199)

    CONCRETE = pygame.Color(149, 165, 166)
    CONCRETE_SHADE = pygame.Color(127, 140, 141)

    # GB
    DARKER_GB = pygame.Color(27, 42, 9)
    DARK_GB = pygame.Color(14, 69, 11)
    LIGHT_GB = pygame.Color(73, 107, 34)
    LIGHTER_GB = pygame.Color(154, 158, 63)

    TRANSPARENT = pygame.Color(0,0,0,0)

    @classmethod
    def __iter__(cls):
        for name, value in vars(cls).items():
            if not name.startswith("__") and isinstance(value, pygame.Color):
                yield value

    @classmethod
    def items(cls):
        """Iterate over (name, color) pairs."""
        for name, value in vars(cls).items():
            if not name.startswith("__") and isinstance(value, pygame.Color):
                yield name, value

    @staticmethod
    def mult(color: pygame.typing.ColorLike , factor: float):
        color = pygame.Color(color)
        return pygame.Color(
            min(max(0, int(color[0] * factor)), 255),
            min(max(0, int(color[1] * factor)), 255),
            min(max(0, int(color[2] * factor)), 255),
            color[3] if len(color)== 4 else 255
        )

    @staticmethod
    def lerp(color1: pygame.Color | tuple[int, int, int, int], color2: pygame.Color | tuple[int, int, int, int], t: float) -> pygame.Color:
        """Linearly interpolate between two colors."""
        t = max(0.0, min(1.0, t))
        c1 = color1 if isinstance(color1, (tuple, list)) else (color1.r, color1.g, color1.b, color1.a)
        c2 = color2 if isinstance(color2, (tuple, list)) else (color2.r, color2.g, color2.b, color2.a)
        return pygame.Color(
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
            int((c1[3] if len(c1) > 3 else 255) + ((c2[3] if len(c2) > 3 else 255) - (c1[3] if len(c1) > 3 else 255)) * t)
        )

    @staticmethod
    def get_name(color_value:pygame.Color):
        for name, val in color.__dict__.items():
            # Only consider attributes that are pygame.Color instances
            if isinstance(val, pygame.Color) and val == color_value:
                return name
        return str(color_value)
    

class easing(Enum):
    LINEAR = (0, 0, 1, 1)
    EASE_IN = (0.95, 0, 1, 0.55)
    EASE_OUT = (0.5, 1, 0.5, 1)
    EASE_IN_OUT = (0.55, 0, 0.45, 1)
    EASE_IN_OUT_ELASTIC = (0.76,-0.36,0.41,1.34)

    def __init__(self, *control_points):
        self.control_points = control_points

    @classmethod
    def create(cls, *control_points):
        """Create a custom easing instance."""
        instance = object.__new__(cls)  
        instance._value_ = control_points
        instance.control_points = control_points
        return instance

class axis(Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class spacing(Enum):
    MIN = "min"
    HALF = "half"
    MAX = "max"
    MANUAL = "manual"


class alignment(Enum):
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    TOP = "top"
    BOTTOM = "bottom"
    TOPLEFT = "topleft"
    TOPRIGHT = "topright"
    MIDLEFT = "midleft"
    MIDRIGHT = "midright"
    MIDTOP = "midtop"
    MIDBOTTOM = "midbottom"
    BOTTOMLEFT = "bottomleft"
    BOTTOMRIGHT = "bottomright"


class direction(Enum):
    LEFT = 0
    UP = 1
    RIGHT = 2
    DOWN = 3


class drawMode(Enum):
    SOLID = 0
    TEXTURED = 1


class debugMode(Enum):
    HIDDEN = 0
    DEBUGGER = 1
    OUTLINES = 2


class actionType(Enum):
    INSTANTANEOUS = 0
    CONTINUOUS = 1
    HOLDING = 2


class textMode(Enum):
    ALPHABETICAL = 0
    NUMERICAL = 1
    ALPHANUMERICAL = 3




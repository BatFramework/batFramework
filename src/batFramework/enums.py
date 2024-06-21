from enum import Enum


class color:
    WHITE = (255, 255, 255)
    LIGHTER_GRAY = (236, 240, 241)
    LIGHT_GRAY = (189, 195, 199)
    DARK_GRAY = (66, 66, 66)
    DARKER_GRAY = (23, 23, 23)
    BLACK = (0, 0, 0)

    TURQUOISE = (26, 188, 156)
    TURQUOISE_SHADE = (22, 160, 133)

    GREEN = (46, 204, 113)
    GREEN_SHADE = (39, 174, 96)

    BLUE = (52, 152, 219)
    BLUE_SHADE = (41, 128, 185)

    PURPLE = (155, 89, 182)
    PURPLE_SHADE = (142, 68, 173)

    CHARCOAL = (52, 73, 94)
    CHARCOAL_SHADE = (44, 62, 80)

    GOLD = (241, 196, 15)
    GOLD_SHADE = (243, 156, 18)

    ORANGE = (230, 126, 34)
    ORANGE_SHADE = (211, 84, 0)

    RED = (231, 76, 60)
    RED_SHADE = (192, 57, 43)

    CLOUD = (236, 240, 241)
    CLOUD_SHADE = (189, 195, 199)

    CONCRETE = (149, 165, 166)
    CONCRETE_SHADE = (127, 140, 141)

    # GB
    DARKER_GB = (27, 42, 9)
    DARK_GB = (14, 69, 11)
    LIGHT_GB = (73, 107, 34)
    LIGHTER_GB = (154, 158, 63)

class easing(Enum):
    LINEAR = (0, 0, 1, 1)
    EASE_IN = (0.95, 0, 1, 0.55)
    EASE_OUT = (0.5, 1, 0.5, 1)
    EASE_IN_OUT = (0.55, 0, 0.45, 1)
    EASE_IN_OUT_ELASTIC = (0.39, -0.55, 0.3, 1.3)

    def __init__(self, *control_points):
        self.control_points = control_points

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
    ALPHANUMERIC = 3 
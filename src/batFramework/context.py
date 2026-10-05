from .utils import Singleton
from .enums import debugMode
from .scene import Scene
from .camera import Camera
from pygame import Clock
class Context:
    current_scene : Scene   = None
    current_camera : Camera = None
    last_dt :float          = None
    debug_mode : debugMode  = debugMode.HIDDEN
    clock : Clock           = None
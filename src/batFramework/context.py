from .utils import Singleton
from .enums import debugMode
from .scene import Scene
from .camera import Camera
class Context:
    current_scene :Scene = None
    current_camera :Camera= None
    last_dt = None
    debug_mode = debugMode.HIDDEN
    
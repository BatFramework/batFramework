import pygame
import batFramework as bf
import sys
from .constants import Constants as const
from .utils import Singleton
from .enums import *
from .resourceManager import ResourceManager
from .fontManager import FontManager
from .utils import Utils as utils
from .tileset import Tileset
from .time import TimeManager, Timer
from .easingController import EasingController
from .cutscene import Cutscene, CutsceneManager
from .cutsceneBlocks import *
from .audioManager import AudioManager
import batFramework.transition as transition
from .action import Action
from .actionContainer import *
from .camera import Camera
from .object import Object
from .entity import Entity
from .renderGroup import RenderGroup
from .dynamicEntity import DynamicEntity
from .sprite import Sprite
from .scrollingSprite import ScrollingSprite
from .particle import *
from .animatedSprite import AnimatedSprite, AnimState
from .stateMachine import State, StateMachine
from .scene import Scene
from .gui import *
from .sceneManager import SceneManager
from .manager import Manager


def init_screen(resolution: tuple[int, int], flags: int = 0, vsync: int = 0):
    const.RESOLUTION = resolution
    const.FLAGS = flags
    const.VSYNC = vsync
    const.SCREEN = pygame.display.set_mode(
        const.RESOLUTION, const.FLAGS, vsync=const.VSYNC
    )
    print(
        f"Window : {resolution[0]}x{resolution[1]} [vsync:{pygame.display.is_vsync()}]"
    )


def init(
    resolution: tuple[int, int],
    flags: int = 0,
    vsync: int = 0,
    default_text_size=None,
    default_font=None,
    resource_path: str | None = None,
    window_title: str = "BatFramework Project",
    fps_limit: int = 0,
):
    pygame.display.set_caption(window_title)
    init_screen(resolution, flags, vsync)

    ResourceManager().set_resource_path(
        resource_path if resource_path is not None else "."
    )
    if resource_path is not None:
        ResourceManager().load_dir(ResourceManager().RESOURCE_PATH)
    if default_text_size is not None:
        FontManager().set_default_text_size(default_text_size)
    FontManager().init_font(default_font)
    const.BF_INITIALIZED = True
    const.set_fps_limit(fps_limit)

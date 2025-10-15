import pathlib
import tomllib
from importlib.metadata import version, PackageNotFoundError

def get_version() -> str:
    try:
        return version("batframework")
    except PackageNotFoundError:
        pyproject = pathlib.Path(__file__).resolve().parent.parent / "pyproject.toml"
        if pyproject.exists():
            with open(pyproject, "rb") as f:
                data = tomllib.load(f)
            return data["project"]["version"]
        return "0.0.0"

__version__ = get_version()


import os
import pygame
import json
import batFramework as bf
from .constants import Constants as const
from .utils import Singleton
from .enums import *
from .resourceManager import ResourceManager
from .fontManager import FontManager
from .utils import Utils as utils
from .tileset import Tileset
from .timeManager import TimeManager,Timer,SceneTimer
from .easingController import EasingController
from .propertyEaser import PropertyEaser
from .cutsceneManager import CutsceneManager
import batFramework.cutscene as cutscene
from .audioManager import AudioManager
import batFramework.transition as transition
from .action import Action
from .actionContainer import *
from .camera import Camera
from .entity import Entity
from .drawable import Drawable
from .renderGroup import RenderGroup
from .dynamicEntity import DynamicEntity
from .sprite import Sprite
from .scrollingSprite import ScrollingSprite
from .particle import *
from .animation import Animation
from .animatedSprite import AnimatedSprite
from .stateMachine import State, StateMachine
from .sceneLayer import SceneLayer
from .scene import Scene
from .baseScene import BaseScene
import batFramework.gui as gui
from .sceneManager import SceneManager
from .manager import Manager
from .templates import *




def init_screen(resolution: tuple[int, int], flags: int = 0, vsync: int = 0):
    const.set_resolution(resolution)
    const.FLAGS = flags
    const.VSYNC = vsync
    const.SCREEN = pygame.display.set_mode(
        const.RESOLUTION, const.FLAGS, vsync=const.VSYNC
    )
    print(
        f"Window : {resolution[0]}x{resolution[1]}"
    )


def print_version():
    print(f"BatFramework version: {__version__}")

def init(
    resolution: tuple[int, int],
    flags: int = 0,
    window_caption: str = "BatFramework Project",
    resource_path: str | None = None,
    default_font_size=None,
    default_font=None,
    fps_limit: int = 0,
    vsync: int = 0,
):
    print_version()
    pygame.display.set_caption(window_caption)
    init_screen(resolution, flags, vsync)
    pygame.mixer.init()
    
    ResourceManager().set_resource_path(
        resource_path if resource_path is not None else "."
    )
    if resource_path is not None:
        ResourceManager().load_resources(ResourceManager().RESOURCE_PATH)
    if default_font_size is not None:
        FontManager().set_default_text_size(default_font_size)
    FontManager().init_font(default_font)
    const.BF_INITIALIZED = True
    const.set_fps_limit(fps_limit)

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
import sys
import logging
import pygame
import json
import batFramework as bf
from .constants import Constants as const
from .utils import Singleton
from .enums import *
from .resourceManager import ResourceManager
from .fontManager import FontManager
from .utils import Utils as utils
from .context import Context
from .tileset import Tileset
from .timeManager import TimeManager, Timer, SceneTimer
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
from .group import Group
from .dynamicEntity import DynamicEntity
from .sprite import Sprite
from .scrollingSprite import ScrollingSprite
from .particle import *
from .animation import Animation
from .animatedSprite import AnimatedSprite
from .stateMachine import State, StateMachine
from .scene import Scene
import batFramework.gui as gui
from .sceneManager import SceneManager
from .manager import Manager
from .templates import *
from .loggingSetup import setup_logging


setup_logging(
    level=logging.DEBUG,
)

logger = logging.getLogger(__name__)

def init(
    resolution: tuple[int, int],
    window_caption: str = "BatFramework Project",
    resource_path: str | None = None,
    default_font=None,
    default_font_size=None,
    fps_limit: int = 0,
    vsync: int = 0,
    flags: int = 0,
):
    def init_screen(resolution: tuple[int, int], flags: int = 0, vsync: int = 0):
        const.set_resolution(resolution)
        const.FLAGS = flags
        const.VSYNC = vsync
        const.SCREEN = pygame.display.set_mode(
            const.RESOLUTION, const.FLAGS, vsync=const.VSYNC
        )
        logger.info(f"Window : {resolution[0]}x{resolution[1]}")

    
    logger.info(f"BatFramework version: {__version__}")
    pygame.display.set_caption(window_caption)
    init_screen(resolution, flags, vsync)
    pygame.mixer.init()

    ResourceManager().set_resource_path(
        resource_path if resource_path is not None else "."
    )
    # if resource_path is not None: TODO
    #     ResourceManager().load_resources(ResourceManager().RESOURCE_PATH)
    if default_font is not None:
        ResourceManager().load_font(default_font)
    if default_font_size is not None:
        FontManager().set_default_text_size(default_font_size)
    FontManager().init_font(default_font)
    const.BF_INITIALIZED = True
    const.set_fps_limit(fps_limit)

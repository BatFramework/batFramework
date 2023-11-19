import pygame
from .constants import Constants as const
import os
import json
initialized = False

def init(
    resolution:tuple[int,int],
    flags:int=0,
    vsync:int = 0,
    default_text_size=None,
    default_font=None,
    resource_path:str|None=None,
    window_title:str="BatFramework Project",
    fps_limit : int = 0
    ):
    global initialized
    if not initialized:
        pygame.init()
        pygame.display.set_caption(window_title)

        # Initialize display
        const.init_screen(resolution,flags,vsync)
        const.set_fps_limit(fps_limit)

        # Initialize default text size
        if default_text_size: const.set_default_text_size(default_text_size)
        # Initialize resource path for game data
        if resource_path: const.set_resource_path(resource_path)

        # Initialize default font cache
        from .utils import Utils
        if default_font is None or isinstance(default_font,str):
            Utils.init_font(default_font)
        else:
            raise ValueError(f"default_font '{default_font}' can be either string or None")
        
        f = list(Utils.FONTS[None].values())[0]
        print(f"Set default font to : {f.name} {'' if default_font is not None else '(default value)'}")
        initialized = True

from .constants import Colors as color
from .constants import Axis as axis
from .utils import Singleton
from .utils import Utils as utils
from .tileset import Tileset
from .time import Time, Timer
from .cutscene import Cutscene,CutsceneManager
from .cutsceneBlocks import *
from .easing import Easing, EasingAnimation
from .audioManager import AudioManager
from .utils import Layout, Alignment, Direction
from .transition import *
from .action import Action
from .actionContainer import ActionContainer
from .camera import Camera
from .entity import Entity
from .dynamicEntity import DynamicEntity
from .animatedSprite import AnimatedSprite, AnimState
from .stateMachine import State, StateMachine
from .particles import Particle, ParticleManager
# from .debugger import Debugger
from .scene import Scene
from .gui import * 
from .sceneManager import SceneManager
from .manager import Manager


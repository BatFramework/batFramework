import pygame
from .constants import Constants as const

initialized = False

def init(
    resolution:tuple[int,int],
    flags:int=0,
    vsync:int = 0,
    default_text_size=None,
    default_font=None,
    resource_path:str|None=None,
    window_title:str="pygame window",
    fps_limit : int = 0
    ):
    global initialized
    if not initialized:
        print("batFramework ver 0.1.9")
        pygame.init()
        pygame.display.set_caption(window_title)
        const.init_screen(resolution,flags,vsync)
        if default_text_size: const.set_default_text_size(default_text_size)
        if resource_path: const.set_resource_path(resource_path)
        from .utils import Utils
        Utils.init_font(default_font)
        # print(Utils.FONTS)
        initialized = True
        const.set_fps_limit(fps_limit)

if not initialized:
    # print("[IMPORTANT] Initialize batFramework after you import 'init' !")
    pass

from .constants import Colors as color
from .utils import *
from .utils import Utils as utils
from .utils import Singleton
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
from .animatedSprite import AnimatedSprite, AnimState
from .stateMachine import State, StateMachine
from .particles import Particle, ParticleManager
# from .debugger import Debugger
from .scene import Scene
from .gui import * 
from .sceneManager import SceneManager
from .manager import Manager


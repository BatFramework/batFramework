import pygame
from .constants import Constants as const

initialized = False


def init(resolution, flags:int=0, vsync:int = 0,default_text_size=None,resource_path:str=None):
    global initialized
    if not initialized:
        pygame.init()
        const.init_screen(resolution,flags,vsync)
        if default_text_size: const.set_default_text_size(default_text_size)
        if resource_path: const.set_resource_path(resource_path)
        initialized = True

if not initialized:
    # print("[IMPORTANT] Initialize batFramework after you import 'init' !")
    pass

from .constants import Colors as color
from .utils import Singleton
from .time import Time, Timer
from .cutscene import Cutscene,CutsceneBlock,CutsceneManager
from .cutsceneBlocks import *
from .utils import *
from .utils import Utils as utils
from .cutscene import CutsceneManager, Cutscene, CutsceneBlock
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
from .gui.interactiveEntity import InteractiveEntity
from .particles import Particle, ParticleManager
from .gui import * 
from .debugger import Debugger
from .scene import Scene
from .sceneManager import SceneManager
from .manager import Manager


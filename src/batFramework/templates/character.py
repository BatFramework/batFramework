from .stateMachine import AnimatedSprite,AnimatedStateMachine
from .controller import PlatformController
import batFramework as bf
import pygame



class PlatformCharacter(bf.AnimatedSprite,PlatformController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.animachine = AnimatedStateMachine(self)
        




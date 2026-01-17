from .stateMachine import AnimatedSprite,AnimatedStateMachine
from .controller import PlatformController
import batFramework as bf
import pygame



class PlatformCharacter(PlatformController,bf.AnimatedSprite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state_machine = AnimatedStateMachine(self)
        



import batFramework as bf
import pygame
from .states import *

class Platform2DCharacter(bf.Character):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.actions = bf.ActionContainer(
            *bf.DirectionalKeyControls(),
            bf.Action("jump").add_key_control(pygame.K_SPACE).set_holding()
        )
        self.on_ground : bool = False
        self.max_jumps = 2
        self.jump_counter = 0
        self.jump_force = 150
        self.speed = 100
        self.acceleration = 30
        self.friction = 0.7
        self.gravity = 300
        self.terminal_velocity = 1000

    def do_setup_animations(self):
        self.add_animation(bf.Animation("idle"))
        self.add_animation(bf.Animation("run"))
        self.add_animation(bf.Animation("jump"))
        self.add_animation(bf.Animation("fall"))


    def do_setup_states(self):
        self.state_machine.add_state(Platform2DIdle())
        self.state_machine.add_state(Platform2DRun())
        self.state_machine.add_state(Platform2DJump())
        self.state_machine.add_state(Platform2DFall())
        self.state_machine.set_state("idle")
        


    def do_reset_actions(self) -> None:
        self.actions.reset()

    def do_process_actions(self, event: pygame.Event) -> None:
        self.actions.process_event(event)
    

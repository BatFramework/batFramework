import batFramework as bf
from pygame.math import Vector2
import pygame
from game_constants import GameConstants as gconst
from level import Level
import utils.tools as tools 
from level import Tile,Level
from player import Player

def horizontal_movement(parent_entity:bf.AnimatedSprite, speed):
    if parent_entity.action_container.is_active("right"):
        parent_entity.set_flipX(False)
    elif parent_entity.action_container.is_active("left"):
        parent_entity.set_flipX(True)
    else:
        return
    if parent_entity.flipX : 
        parent_entity.velocity.x = -speed
    else:
        parent_entity.velocity.x = speed

class Idle(bf.State):
    def __init__(self) -> None:
        super().__init__("idle")
    def on_enter(self):
        self.parent_entity.set_animState("idle")
    def update(self, dt):
        if self.parent_entity.velocity.y > gconst.GRAVITY *dt:
            self.state_machine.set_state("fall")
            self.parent_entity.on_ground =False
            return
        if self.parent_entity.action_container.is_active("up") and self.parent_entity.on_ground:
            self.state_machine.set_state("jump")

        elif self.parent_entity.action_container.is_active("right") or \
            self.parent_entity.action_container.is_active("left"):
            self.state_machine.set_state("run")


class Run(bf.State):
    def __init__(self) -> None:
        super().__init__("run")
    def on_enter(self):
        self.parent_entity.set_animState("run")

    def update(self, dt):
        if self.parent_entity.velocity.y > gconst.GRAVITY *dt:
            self.state_machine.set_state("fall")
            self.parent_entity.on_ground =False
            return
        if not self.parent_entity.action_container.is_active("right") and \
            not self.parent_entity.action_container.is_active("left"):
            self.state_machine.set_state("idle")
            return
        if self.parent_entity.action_container.is_active("up"):
            self.state_machine.set_state("jump")
            return
        horizontal_movement(self.parent_entity,self.parent_entity.h_movement_speed)

class Fall(bf.State):
    def __init__(self) -> None:
        super().__init__("fall")
        # self.h_movement_speed = 50

    def on_enter(self):
        self.parent_entity.set_animState("fall")
    def update(self, dt):
        if self.parent_entity.on_ground:
            self.state_machine.set_state("idle" if self.parent_entity.velocity.x == 0  else "run") 
            return
        horizontal_movement(self.parent_entity,self.parent_entity.h_movement_speed*1.2)

class Jump(bf.State):
    def __init__(self) -> None:
        super().__init__("jump")
        self._jumped = False
        

    def on_enter(self):
        self.parent_entity.set_animState("jump")
        self._jumped = False
    def update(self, dt):
        if self.parent_entity.velocity.y >= 0 and self._jumped:
            self.state_machine.set_state("fall")
            return
        # if not self._jumped and self.parent_entity.float_counter >= 2:
        #     self.parent_entity.velocity.y = -self.parent_entity.jump_force
        #     self._jumped = True
        #     self.parent_entity.on_ground = False
        if not self._jumped:
            self.parent_entity.velocity.y = -self.parent_entity.jump_force
            self._jumped = True
            self.parent_entity.on_ground = False
        horizontal_movement(self.parent_entity,self.parent_entity.h_movement_speed*1.2)


class Baby(Player):
    def __init__(self) -> None:
        # self.set_debug_color("blue")
        super().__init__()
        # bf.AnimatedSprite.__init__(self,(8,16))



    def init_actions(self):
        self.action_container.add_action(
            bf.Action("down").add_key_control(pygame.K_DOWN, pygame.K_s).set_holding(),
            bf.Action("up").add_key_control(pygame.K_UP, pygame.K_w).set_holding(),
            bf.Action("left").add_key_control(pygame.K_LEFT, pygame.K_a).set_holding(),
            bf.Action("right").add_key_control(pygame.K_RIGHT, pygame.K_d).set_holding(),
            bf.Action("spawn").add_key_control(pygame.K_s).set_instantaneous()

        ) 
    def init_animStates(self):
        sprite_size = [int(i) for i in self.rect.size]

        self.add_animState("run","animation/baby/run.png",   sprite_size, [3]*8)
        self.add_animState("idle","animation/baby/idle.png",  sprite_size, [20,15])
        self.add_animState("jump","animation/baby/idle.png",  sprite_size, [5,5])
        self.add_animState("fall","animation/baby/fall.png",  sprite_size, [6,6])

    def init_class_vars(self):

        self.collision_rect = pygame.FRect(0,0,self.rect.w,gconst.TILE_SIZE)
        self.position = Vector2()
        self.velocity :Vector2 = Vector2()
        self.spawn_point = (0,0)
        self.on_ground = False
        self.action_container = bf.ActionContainer()
        self.h_movement_speed = 50
        self.jump_force = 140
        # self.level_link = None
        self.big_sis_link : bf.AnimatedSprite = None
        self.is_held  : bool= False
        self.control = False     

    def init_stateMachine(self):
        self.state_machine :bf.StateMachine = bf.StateMachine(self)
        self.state_machine.add_state(Idle())
        self.state_machine.add_state(Run())
        self.state_machine.add_state(Jump())
        self.state_machine.add_state(Fall())
        self.state_machine.set_state("idle")

    def hold(self,value):
        self.is_held = value


    def do_when_added(self):
        self.level_link : Level = self.parent_scene.get_sharedVar("level")
        self.big_sis_link = self.parent_scene.get_sharedVar("player")
        

    def update(self, dt: float):
        bf.AnimatedSprite.update(self,dt)
        if not self.is_held : 
            self.state_machine.update(dt)
            self.process_physics(dt)
            if not self.control: self.set_flipX(self.big_sis_link.rect.centerx < self.rect.centerx)
        else:
            self.set_flipX(self.big_sis_link.flipX)
            self.set_position(*self.big_sis_link.rect.move(0,-5).midtop)
        self.action_container.reset()
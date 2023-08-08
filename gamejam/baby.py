import batFramework as bf
from pygame.math import Vector2
import pygame
from game_constants import GameConstants as gconst
from level import Level
import utils.tools as tools 
from level import Tile,Level

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
            self.stateMachine.set_state("fall")
            self.parent_entity.on_ground =False
            return
        if self.parent_entity.action_container.is_active("up") and self.parent_entity.on_ground:
            self.stateMachine.set_state("jump")

        elif self.parent_entity.action_container.is_active("right") or \
            self.parent_entity.action_container.is_active("left"):
            self.stateMachine.set_state("run")


class Run(bf.State):
    def __init__(self) -> None:
        super().__init__("run")
    def on_enter(self):
        self.parent_entity.set_animState("run")

    def update(self, dt):
        if self.parent_entity.velocity.y > gconst.GRAVITY *dt:
            self.stateMachine.set_state("fall")
            self.parent_entity.on_ground =False
            return
        if not self.parent_entity.action_container.is_active("right") and \
            not self.parent_entity.action_container.is_active("left"):
            self.stateMachine.set_state("idle")
            return
        if self.parent_entity.action_container.is_active("up"):
            self.stateMachine.set_state("jump")
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
            self.stateMachine.set_state("idle" if self.parent_entity.velocity.x == 0  else "run") 
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
            self.stateMachine.set_state("fall")
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


class Baby(bf.AnimatedSprite):
    def __init__(self) -> None:
        super().__init__((8,16))
        self.set_debug_color("blue")
        self.collision_rect = pygame.FRect(0,0,*self.rect.size)
        self.position = Vector2()
        self.velocity :Vector2 = Vector2()
        self.spawn_point = (0,0)
        self.on_ground = False
        self.action_container = bf.ActionContainer()
        self.h_movement_speed = 50
        self.jump_force = 170


        self.action_container.add_action(
            bf.Action("down").add_key_control(pygame.K_DOWN, pygame.K_s).set_holding(),
            bf.Action("up").add_key_control(pygame.K_UP, pygame.K_w).set_holding(),
            bf.Action("left").add_key_control(pygame.K_LEFT, pygame.K_a).set_holding(),
            bf.Action("right").add_key_control(pygame.K_RIGHT, pygame.K_d).set_holding(),
            bf.Action("spawn").add_key_control(pygame.K_s).set_instantaneous()

        )

        sprite_size = [int(i) for i in self.rect.size]

        self.add_animState("run","animation/baby/idle.png",   sprite_size, [5,5])
        self.add_animState("idle","animation/baby/idle.png",  sprite_size, [20,15])
        self.add_animState("jump","animation/baby/idle.png",  sprite_size, [5,5])
        self.add_animState("fall","animation/baby/idle.png",  sprite_size, [5,5])
        self.add_animState("hide","animation/baby/idle.png",  sprite_size, [5,5])



        self.stateMachine :bf.StateMachine = bf.StateMachine(self)
        self.stateMachine.add_state(Idle())
        self.stateMachine.add_state(Run())
        self.stateMachine.add_state(Jump())
        self.stateMachine.add_state(Fall())
        self.stateMachine.set_state("idle")
 
        self.level_link = None
        self.big_sis_link : bf.AnimatedSprite = None
        self.is_held  : bool= False

    def hold(self,value):
        self.is_held = value


    def do_when_added(self):
        self.level_link : Level = self.parent_scene.get_sharedVar("level")
        self.big_sis_link = self.parent_scene.get_sharedVar("player")
        

    def get_bounding_box(self):
        return self.rect,self.collision_rect


    def process_event(self, event):
        self.action_container.process_event(event)

    def set_position(self, x, y):
        self.position.update(x,y)
        self.rect.center = x,y
        self.collision_rect.midbottom = self.rect.midbottom



    def on_collideX(self,collider: bf.Entity):
        if self.velocity.x >= 0:
            self.collision_rect.right = collider.rect.left
        elif self.velocity.x < 0:
            self.collision_rect.left = collider.rect.right
        self.velocity.x = 0
        self.position.x= self.collision_rect.left

    def on_collideY(self,collider:bf.Entity):
        if self.velocity.y < 0:
            self.collision_rect.top = collider.rect.bottom
        elif self.velocity.y >= 0:
            if not self.on_ground:

                self.collision_rect.bottom = collider.rect.top
                self.position.y = self.collision_rect.top
                self.on_ground = True
            else:
                # Adjust the position if the player is already on the ground
                self.collision_rect.bottom = collider.rect.top
        self.velocity.y = 0
        self.position.y = self.collision_rect.top
    def process_physics(self,dt):
        
        #--------------X AXIS
        #apply velocity
        self.collision_rect.x += self.velocity.x * (dt)

        #get level tiles
        near_tiles : list[Tile]= self.level_link.get_neighboring_tiles(*tools.world_to_grid(*[int(i) for i in self.collision_rect.center]))
        #get level entities
        near_tiles.extend(self.level_link.get_neighboring_entities(*self.collision_rect.center,max(self.rect.size)))

        near_tiles = [tile for tile in near_tiles if tile!=None and tile.has_tag("collider")]
        if any(near_tiles):
            collider = self.collision_rect.collidelist(near_tiles)
            if collider > -1: self.on_collideX(near_tiles[collider])
        
        self.rect.centerx = self.collision_rect.centerx

        #--------------Y AXIS

        #GRAVITY
        self.velocity.y = min(self.velocity.y + gconst.GRAVITY * dt, (gconst.GRAVITY // 5))
        #apply velocity
        self.collision_rect.y += self.velocity.y * (dt)
        # print(self.collision_rect)


        near_tiles = self.level_link.get_neighboring_tiles(*tools.world_to_grid(*[int(i) for i in self.collision_rect.center]))
        near_tiles.extend(self.level_link.get_neighboring_entities(*self.collision_rect.center,max(self.rect.size)))

        near_tiles = [tile for tile in near_tiles if tile!=None and tile.has_tag("collider")]
        if any(near_tiles):
            collider = self.collision_rect.collidelist(near_tiles)
            if collider > -1: self.on_collideY(near_tiles[collider])

        self.rect.bottom = self.collision_rect.bottom
        
        self.velocity.x *= (gconst.FRICTION )

        if abs(self.velocity.x) < 0.02:
            self.velocity.x = 0
        if abs(self.velocity.y) < 0.02:
            self.velocity.y = 0

        self.set_position(*[round(i,1) for i in self.rect.center])

    def update(self, dt: float):
        super().update(dt)
        # self.stateMachine.update(dt)
        if not self.is_held : 
            self.process_physics(dt)
            self.set_flipX(self.big_sis_link.rect.centerx < self.rect.centerx)
        else:
            self.set_flipX(self.big_sis_link.flipX)
            self.set_position(*self.big_sis_link.rect.move(0,-5).midtop)
        self.action_container.reset()
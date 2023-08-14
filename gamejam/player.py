import batFramework as bf
from pygame.math import Vector2
import pygame
from game_constants import GameConstants as gconst
from level import Level, Tile
import utils.tools as tools
import itertools


def horizontal_movement(parent_entity: bf.AnimatedSprite, speed):
    if parent_entity.action_container.is_active("right"):
        parent_entity.set_flipX(False)
    elif parent_entity.action_container.is_active("left"):
        parent_entity.set_flipX(True)
    else:
        return
    if parent_entity.flipX:
        parent_entity.velocity.x = -speed
    else:
        parent_entity.velocity.x = speed


class Idle(bf.State):
    def __init__(self) -> None:
        super().__init__("idle")

    def on_enter(self):
        self.parent_entity.set_animState("idle")

    def update(self, dt):
        if self.parent_entity.velocity.y > gconst.GRAVITY * 1.5 * dt:
            self.state_machine.set_state("fall")
            self.parent_entity.on_ground = False
            return
        if (
            self.parent_entity.action_container.is_active("up")
            and self.parent_entity.on_ground
        ):
            self.state_machine.set_state("jump")

        elif self.parent_entity.action_container.is_active(
            "right"
        ) or self.parent_entity.action_container.is_active("left"):
            self.state_machine.set_state("run")


class Run(bf.State):
    def __init__(self) -> None:
        super().__init__("run")
        self.incrementer = (i for i in itertools.count())

    def on_enter(self):
        self.parent_entity.set_animState("run")

    def update(self, dt):
        if self.parent_entity.velocity.y > gconst.GRAVITY * 1.5 * dt:
            self.state_machine.set_state("fall")
            self.parent_entity.on_ground = False
            return
        if not self.parent_entity.action_container.is_active(
            "right"
        ) and not self.parent_entity.action_container.is_active("left"):
            self.state_machine.set_state("idle")
            return
        if self.parent_entity.action_container.is_active("up"):
            self.state_machine.set_state("jump")
            return
        horizontal_movement(self.parent_entity, self.parent_entity.h_movement_speed)
        if next(self.incrementer) % 10 == 0:
            bf.AudioManager().play_sound("step", 0.5)


class Fall(bf.State):
    def __init__(self) -> None:
        super().__init__("fall")
        # self.h_movement_speed = 50

    def on_enter(self):
        self.parent_entity.set_animState("fall")

    def update(self, dt):
        if self.parent_entity.on_ground:
            bf.AudioManager().play_sound("step")
            self.state_machine.set_state(
                "idle" if self.parent_entity.velocity.x == 0 else "run"
            )
            return
        horizontal_movement(
            self.parent_entity, self.parent_entity.h_movement_speed * 1.2
        )


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
        if not self._jumped and self.parent_entity.float_counter >= 4:
            self.parent_entity.velocity.y = -self.parent_entity.jump_force
            self._jumped = True
            self.parent_entity.on_ground = False
            bf.AudioManager().play_sound("jump", 0.5)
        horizontal_movement(
            self.parent_entity, self.parent_entity.h_movement_speed * 1.2
        )


class Player(bf.AnimatedSprite):
    def __init__(self) -> None:
        super().__init__((8, 16))
        self.set_debug_color("blue")

        self.init_class_vars()
        self.init_actions()
        self.init_animStates()
        self.init_stateMachine()

        self.level_link = None
        self.render_order = 3

    def init_class_vars(self):
        self.position = Vector2()
        self.velocity: Vector2 = Vector2()
        self.spawn_point = (0, 0)
        self.on_ground = False
        self.action_container = bf.ActionContainer()
        self.h_movement_speed = 40
        self.jump_force = 170
        self.control = True
        self.collision_rect = pygame.FRect(0, 0, *self.rect.size)
        self.baby_link: "Player" = None
        self.fade_surf = pygame.Surface(self.rect.size,flags=pygame.SRCALPHA)
        self.fade_in_transition = bf.EasingAnimation(bf.Easing.EASE_OUT,500,lambda x: print(x),self.end_fade_in_transition)
    
    def end_fade_in_transition(self):
        self.fade_in_transition.stop()
        self.set_center(*self.baby_link.rect.midtop)

    def warp(self):
        if self.fade_in_transition.is_over() or self.fade_in_transition.start_time is None:
            self.fade_in_transition.reset()
            self.fade_in_transition.start()

    def init_actions(self):
        self.action_container.add_action(
            bf.Action("down").add_key_control(pygame.K_DOWN, pygame.K_s).set_holding(),
            bf.Action("up").add_key_control(pygame.K_UP, pygame.K_w).set_holding(),
            bf.Action("left").add_key_control(pygame.K_LEFT, pygame.K_a).set_holding(),
            bf.Action("right")
            .add_key_control(pygame.K_RIGHT, pygame.K_d)
            .set_holding(),
            bf.Action("spawn").add_key_control(pygame.K_s).set_instantaneous(),
            bf.Action("hold").add_key_control(pygame.K_SPACE),
        )

    def init_animStates(self):
        sprite_size = [int(i) for i in self.rect.size]

        self.add_animState("idle", "animation/player/idle.png", sprite_size, [20, 15])
        self.add_animState("run", "animation/player/run.png", sprite_size, [3] * 8)
        self.add_animState("jump", "animation/player/jump.png", sprite_size, [4, 9999])
        self.add_animState("fall", "animation/player/fall.png", sprite_size, [6, 6])

    def init_stateMachine(self):
        self.state_machine: bf.StateMachine = bf.StateMachine(self)
        self.state_machine.add_state(Idle())
        self.state_machine.add_state(Run())
        self.state_machine.add_state(Jump())
        self.state_machine.add_state(Fall())
        self.state_machine.set_state("idle")

    def do_when_added(self):
        self.level_link: Level = self.parent_scene.get_sharedVar("level")
        self.baby_link = self.parent_scene.get_sharedVar("baby")

    def get_bounding_box(self):
        return self.rect, self.collision_rect

    def set_control(self, value: bool):
        self.action_container.hard_reset()
        self.control = value

    def reset_actions(self):
        self.action_container.hard_reset()

    def process_event(self, event):
        if self.control:
            self.action_container.process_event(event)

    def set_position(self, x, y):
        self.position.update(x, y)
        self.rect.center = x, y
        self.collision_rect.midbottom = self.rect.midbottom

    def set_on_ground(self, value: bool):
        self.on_ground = value

    def on_collideX(self, collider: bf.Entity):
        if not collider.on_collideX(self):
            return False
        if self.velocity.x >= 0:
            self.collision_rect.right = collider.rect.left
        elif self.velocity.x < 0:
            self.collision_rect.left = collider.rect.right
        self.velocity.x = 0
        self.position.x = self.collision_rect.left
        return True

    def on_collideY(self, collider: bf.Entity):
        if not collider.on_collideY(self):
            return False

        if self.velocity.y < 0:
            self.collision_rect.top = collider.rect.bottom
        elif self.velocity.y >= 0:
            if not self.on_ground:
                self.collision_rect.bottom = collider.rect.top
                self.position.y = self.collision_rect.top
                self.on_ground = True
                pygame.event.post(
                    pygame.event.Event(gconst.STEP_ON_EVENT, {"entity": collider})
                )
            else:
                # Adjust the position if the player is already on the ground
                self.collision_rect.bottom = collider.rect.top
        self.velocity.y = 0
        self.position.y = self.collision_rect.top
        return True

    def process_physics(self, dt):
        # --------------Y AXIS

        # GRAVITY
        self.velocity.y = min(
            self.velocity.y + gconst.GRAVITY * dt, (gconst.GRAVITY // 5)
        )
        # apply velocity
        self.collision_rect.y += self.velocity.y * (dt)
        # print(self.collision_rect)

        near_tiles = self.level_link.get_neighboring_tiles(
            *tools.world_to_grid(*[int(i) for i in self.collision_rect.center])
        )
        near_tiles.extend(
            self.level_link.get_neighboring_entities(
                *self.collision_rect.center, max(self.rect.size)
            )
        )
        near_tiles = [
            tile for tile in near_tiles if tile != None and tile.has_tag("collider")
        ]
        if any(near_tiles):
            colliders = [
                i for i in self.collision_rect.collidelistall(near_tiles) if i > -1
            ]
            for collider in colliders:
                if self.on_collideY(near_tiles[collider]):
                    break

        self.rect.bottom = self.collision_rect.bottom

        # --------------X AXIS

        # apply velocity
        self.collision_rect.x += self.velocity.x * (dt)

        near_tiles: list[Tile] = self.level_link.get_neighboring_tiles(
            *tools.world_to_grid(*[int(i) for i in self.collision_rect.center])
        )
        near_tiles.extend(
            self.level_link.get_neighboring_entities(
                *self.collision_rect.center, max(self.rect.size)
            )
        )

        near_tiles = [
            tile for tile in near_tiles if tile != None and tile.has_tag("collider")
        ]

        if any(near_tiles):
            colliders = [
                i for i in self.collision_rect.collidelistall(near_tiles) if i > -1
            ]
            for collider in colliders:
                if self.on_collideX(near_tiles[collider]):
                    break

        self.rect.centerx = self.collision_rect.centerx

        self.velocity.x *= gconst.FRICTION

        if abs(self.velocity.x) < 0.02:
            self.velocity.x = 0
        if abs(self.velocity.y) < 0.02:
            self.velocity.y = 0

        self.set_position(*[round(i, 1) for i in self.rect.center])

    def update(self, dt: float):
        super().update(dt)
        self.fade_in_transition.update()
        self.state_machine.update(dt)
        self.process_physics(dt)
        if not self.control:
            self.set_flipX(self.baby_link.rect.centerx < self.rect.centerx)
        if self.action_container.is_active("hold"):
            # print("SPACE")
            if self.baby_link.is_held == False:
                if self.rect.colliderect(self.baby_link.rect):
                    self.baby_link.hold(True)
                    bf.AudioManager().play_sound("pick_up")
            else:
                self.baby_link.hold(False)
                self.baby_link.velocity.update(180, -50)
                if self.flipX:
                    self.baby_link.velocity.x *= -1

        self.action_container.reset()

    def draw(self, camera: bf.Camera) -> bool:  
        i = super().draw(camera)
        if not self.fade_in_transition.is_over():
            mask = pygame.mask.from_surface(self.get_state().get_frame(self.float_counter,self.flipX))
            surf = mask.to_surface(setcolor = bf.color.CLOUD_WHITE,unsetcolor=None)
            camera.surface.blit(
                surf,
                camera.transpose(self.rect),
            )
        return i
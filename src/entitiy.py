import pygame
from pygame.math import Vector2
from .anchor import Anchor
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from scene import Scene
    from scene_manager import SceneManager



class Entity(pygame.sprite.Sprite):
    def __init__(self) -> None:
        super().__init__()
        self._is_hud = False
        self.image: pygame.surface.Surface = pygame.Surface((1, 1))
        self.rect: pygame.rect.Rect = self.image.get_rect()
        self._anchor: int = Anchor.TOPLEFT
        self._is_visible: bool = True
        self.position :Vector2= Vector2()
        self.velocity :Vector2= Vector2()
        self._tags: list[str] = []
        self._id: str = None
        self._lock_size: bool = False
        self._sceneManagerLink :SceneManager = None
        self._sceneLink :Scene= None
        self._gravityAffected :bool= False
        self._has_collision :bool= False
        self._is_collider: bool = False
        self._parentContainer :Entity= None
        self._auto_resize :bool = True # set to false when set_size is called at least once, will prevent resizing after that

    def set_auto_resize(self,val: bool):
        self._auto_resize = val

    def has_auto_resize(self)-> bool:
        return self._auto_resize

    def set_has_collision(self, value: bool):
        self._has_collision = value

    def has_collision(self) -> bool:
        return self._has_collision

    def set_gravity_affected(self, value: bool):
        self._gravityAffected = value
        if value:
            self._is_collider = False

    def is_gravity_affected(self) -> bool:
        return self._gravityAffected

    def set_is_collider(self, value: bool):
        self._is_collider = value
        if value:
            self._gravityAffected = False

    def set_id(self, str: str) -> None:
        self._id = str

    def get_id(self) -> str:
        return self._id

    def add_tag(self, tag: str) -> None:
        self._tags.append(tag)

    def has_tag(self, tag: str) -> bool:
        return tag in self._tags

    def is_collider(self) -> bool:
        return self._is_collider

    def get_collider(self) -> list[pygame.Rect]:
        return [self.rect]

    def set_scene_manager_link(self, managerLink):
        self._sceneManagerLink = managerLink

    def get_scene_manager_link(self):
        return self._sceneManagerLink

    def set_scene_link(self, sceneLink):
        self._sceneLink = sceneLink

    def get_scene_link(self):
        return self._sceneLink

    def lock_size(self):
        self._lock_size = True

    def unlock_size(self):
        self._lock_size = False

    def isSizeLocked(self) -> bool:
        return self._lock_size

    def get_rect(self):
        return self.rect

    def set_hud(self, value: bool):
        self._is_hud = value

    def is_visible(self) -> bool:
        return self._is_visible

    def set_visible(self, val: bool):
        self._is_visible = val

    def is_hud(self):
        return self._is_hud

    def set_size(self, width, height) -> bool:
        if self.isSizeLocked():return False
        self.rect.size = (width,height)
        self.set_position(*self.get_position())
        return True

    # Do NOT change anchor for collision/gravity affected sprites
    def set_anchor(self, anchor: int):
        self._anchor = anchor
        self.set_position(*self.get_position())

    def set_velocity(self, x, y):
        self.velocity.update(x, y)

    def get_velocity(self) -> Vector2:
        return self.velocity

    def apply_velocity_x(self, dt):
        self.position.x += self.velocity.x * dt
        self.set_position(*self.position)

    def apply_velocity_y(self, dt):
        self.position.y += self.velocity.y * dt
        self.set_position(*self.position)

    def add_velocity(self, x, y):
        self.velocity += Vector2(x, y)

    def set_position(self, x, y):
        self.position.update(x, y)
        match self._anchor:
            case Anchor.TOPLEFT:
                self.rect.topleft = self.position
            case Anchor.TOPRIGHT:
                self.rect.topright = self.position
            case Anchor.TOPMID:
                self.rect.midtop = self.position
            case Anchor.CENTER:
                self.rect.center = self.position
            case Anchor.BOTTOMLEFT:
                self.rect.bottomleft = self.position
            case Anchor.BOTTOMRIGHT:
                self.rect.bottomright = self.position
            case Anchor.LEFTMID:
                self.rect.midleft = self.position

            case _:
                print("current anchor is not supported :(")
                exit(1)

    def get_size(self):
        return self.rect.size

    def get_position(self):
        return self.position

    # return value : True  = consume event
    def on_event(self, event: pygame.event.Event) -> bool:
        return False
    def on_key_down(self, key):
        pass

    def on_key_up(self, key):
        pass

    def update(self, dt: float):
        pass

    def draw(self, camera):
        if not self.is_visible():
            return
        camera.blit_entity(self)

    def on_collision_x(self, collider: pygame.Rect):
        if self.get_velocity().x > 0:
            self.rect.right = collider.left
        else:
            self.rect.left = collider.right
        self.position.update(self.rect.topleft)
        self.set_velocity(0, self.get_velocity().y)

    def on_collision_y(self, collider: pygame.Rect):
        if self.get_velocity().y > 0:
            self.rect.bottom = collider.top
        else:
            self.rect.top = collider.bottom
        self.position.update(self.rect.topleft)
        self.set_velocity(self.get_velocity().x, 0)

    def set_parent_container(self, parent):
        self._parentContainer = parent

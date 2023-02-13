import pygame

from . import lib as lib
from .entitiy import Entity


class AnimatedSprite(Entity):
    def __init__(self, *groups: pygame.sprite.AbstractGroup) -> None:
        super().__init__(*groups)
        self._animations: dict[str : pygame.surface.Surface] = {}

        self._animationTimings: dict[str : list[int]] = {}
        self.state = None
        self._animationCounter = 0
        self._animationSpeed = 60
        self._hasFlipX = False
        self._facingRight = True
        self._is_state_locked = False

    def apply_velocity_x(self, dt):
        super().apply_velocity_x(dt)

        if self.velocity.x != 0:
            self._facingRight = self.velocity.x > 0

    def enable_flip_x(self):
        self._hasFlipX = True
        tmp = self._animations
        self._animations = {}
        for key, item in tmp.items():
            self._animations[key] = {
                "facingRight": [surf for surf in item],
                "facingLeft": [
                    pygame.transform.flip(surf, True, False) for surf in item
                ],
            }

    def set_animation_speed(self, value: int):
        self._animationSpeed = value

    def lock_state(self):
        self._is_state_locked = True

    def unlock_state(self):
        self._is_state_locked = False

    def is_state_locked(self) -> bool:
        return self._is_state_locked

    def get_state(self) -> str:
        return self.state

    def get_animation_index(self) -> int:
        tmp = 0
        for index, value in enumerate(self._animationTimings[self.state]):
            if self._animationCounter < tmp + value:
                return index
            tmp += value
        return 0

    def get_animation_max_frames(self) -> int:
        return sum(self._animationTimings[self.state])

    def set_state(self, name: str, resetAnimationCounter=False):
        if self.is_state_locked():
            return
        if name not in self._animations:
            print("Invalid state : ", name)
            exit(1)
        if name == self.state and not resetAnimationCounter:
            return
        if resetAnimationCounter:
            self._animationCounter = 0
        self.state = name

    def load_animation(self, name, path: str, width: int, height: int) -> None:
        res = lib.slicer(path, width, height)
        self.set_size(*res[0].get_size())
        self._animations[name] = res
        self._animationTimings[name] = [10 for _ in res]

    def set_animation_timing(self, name, *timings) -> None:
        if name not in self._animationTimings:
            print("Invalid state : ", name)
            exit(1)
        self._animationTimings[name] = timings

    def update(self, dt: float):
        self._animationCounter += dt * self._animationSpeed
        if self._animationCounter > self.get_animation_max_frames():
            self._animationCounter = 0

    def draw(self, camera):
        if self._hasFlipX:
            direction = "facingRight" if self._facingRight else "facingLeft"
            self.image = self._animations[self.state][direction][
                self.get_animation_index()
            ]
        else:
            self.image = self._animations[self.state][self.get_animation_index()]

        super().draw(camera)

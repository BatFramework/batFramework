import pygame
import batFramework as bf
from typing import Self


class DynamicEntity(bf.Entity):
    def __init__(
        self,
        *args,**kwargs
    ) -> None:
        super().__init__(*args,**kwargs)
        self.velocity = pygame.math.Vector2(0, 0)
        self.ignore_collisions : bool = False

    def on_collideX(self, collider: "DynamicEntity"):
        """
        Return true if collision
        """
        return False

    def on_collideY(self, collider: "DynamicEntity"):
        """
        Return true if collision
        """
        return False

    def move_by_velocity(self, dt) -> None:
        self.set_position(
            self.rect.x + self.velocity.x * dt, self.rect.y + self.velocity.y * dt
        )

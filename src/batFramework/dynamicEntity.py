import pygame
import batFramework as bf
from typing import Self


class DynamicEntity(bf.Entity):
    def __init__(
        self,
        size: None | tuple[int, int] = None,
        surface_flags: int = 0,
        convert_alpha: bool = False,
    ) -> None:
        super().__init__(size, surface_flags, convert_alpha)
        self.velocity = pygame.math.Vector2(0, 0)

    def on_collideX(self, collider: Self):
        return False

    def on_collideY(self, collider: Self):
        return False

    def move_by_velocity(self, dt) -> None:
        self.set_position(
            self.rect.x + self.velocity.x * dt, self.rect.y + self.velocity.y * dt
        )

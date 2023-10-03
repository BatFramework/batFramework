import pygame
import batFramework as bf


class DynamicEntity(bf.Entity):
    def __init__(
        self,
        size : None|tuple[int,int]=None,
        no_surface : bool   =False,
        surface_flags : int =0,
        convert_alpha : bool=False
    ) -> None:
        super().__init__(size,no_surface,surface_flags,convert_alpha)
        self.velocity = pygame.math.Vector2(0, 0)

    def on_collideX(self, collider: "DynamicEntity"):
        return False

    def on_collideY(self, collider: "DynamicEntity"):
        return False


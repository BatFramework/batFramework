from typing import Self, Iterator
from pygame.math import Vector2
import batFramework as bf
import pygame


class ScrollingSprite(bf.Sprite):
    def __init__(
        self,
        data: pygame.Surface | str,
        size: None | tuple[int, int] = None,
        convert_alpha: bool = True,
    ):
        self.scroll_value = Vector2(0, 0)
        self.auto_scroll = Vector2(0, 0)

        # Use integer values for the starting points, converted from floating point scroll values

        super().__init__(data, size, convert_alpha)
        self.original_width, self.original_height = self.original_surface.get_size()

    def get_debug_outlines(self):
        yield from super().get_debug_outlines()
        for r in self._get_mosaic_rect_list():
            yield r.move(*self.rect.topleft)

    def set_image(
        self, data: pygame.Surface | str, size: None | tuple[int, int] = None
    ) -> Self:
        super().set_image(data, size)
        self.original_width, self.original_height = self.original_surface.get_size()
        return self

    def set_autoscroll(self, x: float, y: float) -> Self:
        self.auto_scroll.update(x, y)
        return self

    def set_scroll(self, x: float = None, y: float = None) -> Self:
        self.scroll_value.update(
            x if x else self.scroll_value.x, y if y else self.scroll_value.y
        )
        return self

    def scroll(self, x: float, y: float) -> Self:
        self.scroll_value += x, y
        return self

    def update(self, dt: float) -> None:
        if self.auto_scroll:
            self.scroll(*self.auto_scroll * dt)
        original_width, original_height = self.original_surface.get_size()

        # Use integer values for the starting points, converted from floating point scroll values

        if self.scroll_value.x > self.original_width:
            self.scroll_value.x -= self.original_width
        if self.scroll_value.y > self.original_height:
            self.scroll_value.y -= self.original_height

        super().update(dt)

    def set_size(self, size: tuple[int | None, int | None]) -> Self:
        size = list(size)
        if size[0] is None: size[0] = self.rect.w
        if size[1] is None: size[1] = self.rect.h

        self.surface = pygame.Surface(size).convert_alpha()
        self.rect = self.surface.get_frect(center=self.rect.center)
        return self

    def _get_mosaic_rect_list(self) -> Iterator[pygame.Rect]:
        # Use integer values for the starting points, converted from floating point scroll values
        start_x = int(self.scroll_value.x % self.original_width)
        start_y = int(self.scroll_value.y % self.original_height)

        # Adjust start_x and start_y to begin tiling off-screen to the top-left, covering all visible area
        if start_x != 0:
            start_x -= self.original_width
        if start_y != 0:
            start_y -= self.original_height

        # Set the region in which to tile
        end_x = self.rect.w
        end_y = self.rect.h

        # Starting y_position for the inner loop
        y_position = start_y

        # if self.rect.w-1 < self.scroll_value.x < self.rect.w+1 : print(self.scroll_value.x,int(self.scroll_value.x % self.rect.w),start_x,self.rect.w,original_width)
        # Generate all necessary rectangles
        x = start_x
        while x < end_x:
            y = y_position
            while y < end_y:
                yield pygame.Rect(x, y, self.original_width, self.original_height)
                y += self.original_height
            x += self.original_width
        return self

    def draw(self, camera: bf.Camera) -> int:
        if not (
            self.visible
            and (self.surface is not None)
            and camera.rect.colliderect(self.rect)
        ):
            return 0
        self.surface.fill((0, 0, 0, 0))
        self.surface.fblits(
            [(self.original_surface, r) for r in self._get_mosaic_rect_list()]
        )
        # pygame.draw.rect(camera.surface,"green",next(self._get_mosaic_rect_list()).move(*self.rect.topleft),1)
        camera.surface.blit(self.surface, camera.world_to_screen(self.rect))
        return 1

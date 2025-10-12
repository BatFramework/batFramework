import batFramework as bf
import pygame
from typing import Callable, Iterator


class RenderGroup(bf.Drawable):
    def __init__(
        self, entity_iterator: Callable[[], Iterator[bf.Drawable]], blit_flags: int = 0
    ) -> None:
        super().__init__()
        self.entity_iterator = entity_iterator
        self.blit_flags = blit_flags
        self.set_debug_color("white")

    def draw(self, camera: bf.Camera) -> None:
        if not self.visible:
            return

        fblits_data = []
        for e in self.entity_iterator():
            if not getattr(e, "drawn_by_group", False):
                # Set flag to skip their individual draw call
                e.drawn_by_group = True

            if e.visible and camera.rect.colliderect(e.rect):
                fblits_data.append(
                    (e.surface, (e.rect.x - camera.rect.x, e.rect.y - camera.rect.y))
                )

        camera.surface.fblits(fblits_data, self.blit_flags)

    def get_debug_outlines(self):
        for e in self.entity_iterator():
            yield from e.get_debug_outlines()

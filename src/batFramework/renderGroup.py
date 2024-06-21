import batFramework as bf
import pygame
from typing import Self, Iterator, Callable

"""
+ same render order
+ fblits
"""

class RenderGroup(bf.Entity):
    def __init__(self, entity_iterator: Callable[[],Iterator[bf.Entity]], blit_flags: int = 0) -> None:
        super().__init__()
        self.entity_iterator = entity_iterator
        self.set_blit_flags(blit_flags)
        self.set_debug_color("white")

    def get_debug_outlines(self):
        # yield (self.rect, self.debug_color)
        for e in self.entity_iterator():
            yield from e.get_debug_outlines()

    def set_parent_scene(self, scene) -> Self:
        self.parent_scene = scene
        for e in self.entity_iterator():
            e.set_parent_scene(scene)
        return self

    def process_event(self, event: pygame.Event) -> bool:
        """
        Returns bool : True if the method is blocking (no propagation to next children of the scene)
        """
        self.do_process_actions(event)
        res = self.do_handle_event(event)
        if res:
            return res
        for e in self.entity_iterator():
            if e.process_event(event):
                return True
        return False

    def update(self, dt: float) -> None:
        """
        Update method to be overriden by subclasses of entity
        """
        for e in self.entity_iterator():
            e.update(dt)
        # gen = self.entity_iterator()
        # self.rect = next(gen).rect.unionall([e.rect for e in gen])

        self.do_update(dt)
        self.do_reset_actions()

    def draw(self, camera: bf.Camera) -> None:
        """
        Draw the entity onto the camera with coordinate transposing
        """
        if not self.visible:
            return
        fblits_data = (
            (e.surface, (e.rect.x - camera.rect.x,e.rect.y - camera.rect.y)) for e in self.entity_iterator() if camera.rect.colliderect(e.rect)
        )
        camera.surface.fblits(fblits_data, self.blit_flags)

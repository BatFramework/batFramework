from typing import Any, Self
import pygame
import batFramework as bf
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .camera import Camera


class Entity:
    _count: int = 0
    _available_uids: set[int] = set()


    def __init__(self,*args,**kwargs) -> None:
        if Entity._available_uids:
            self.uid = Entity._available_uids.pop()
        else:
            self.uid = Entity._count
            Entity._count += 1

        self.rect = pygame.FRect(0, 0, 0, 0)
        self.tags: list[str] = []
        self.parent_scene: bf.Scene | None = None
        self.debug_color: tuple | str = "red"

    def __del__(self):
        try:
            Entity._available_uids.add(self.uid)
        except AttributeError:
            pass
    def set_position(self, x, y) -> Self:
        self.rect.topleft = x, y
        return self

    def set_center(self, x, y) -> Self:
        self.rect.center = x, y
        return self

    def get_debug_outlines(self):
        yield (self.rect, self.debug_color)

    def set_debug_color(self, color) -> Self:
        self.debug_color = color
        return self

    def set_parent_scene(self, scene) -> Self:
        if scene == self.parent_scene:
            return self
        if self.parent_scene is not None:
            self.do_when_removed()
        self.parent_scene = scene
        if scene is not None:
            self.do_when_added()
        return self

    def do_when_added(self):
        pass

    def do_when_removed(self):
        pass

    def add_tags(self, *tags) -> Self:
        for tag in tags:
            if tag not in self.tags:
                self.tags.append(tag)
        self.tags.sort()
        return self

    def remove_tags(self, *tags):
        self.tags = [tag for tag in self.tags if tag not in tags]

    def has_tags(self, *tags) -> bool:
        return all(tag in self.tags for tag in tags)

    def get_tags(self) -> list[str]:
        return self.tags

    def process_event(self, event: pygame.Event) -> None:
        if event.consumed:
            return
        self.do_process_actions(event)
        self.do_handle_event(event)

    def do_process_actions(self, event: pygame.Event) -> None:
        """
        Process entity actions you may have set
        """

    def do_reset_actions(self) -> None:
        """
        Reset entity actions you may have set
        """

    def do_handle_event(self, event: pygame.Event):
        """
        Handle specific events with no action support
        """
        return False

    def update(self, dt: float) -> None:
        """
        Update method to be overriden by subclasses of Entity (must call do_update and do_reset_actions)
        """
        self.do_update(dt)
        self.do_reset_actions()

    def do_update(self, dt: float) -> None:
        """
        Update method to be overriden for specific behavior by the end user
        """

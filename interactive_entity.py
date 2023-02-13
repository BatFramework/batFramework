import pygame

from batFramework import constants as c
from batFramework.camera import Camera

from .entitiy import Entity


class InteractiveEntity(Entity):
    def __init__(self) -> None:
        Entity.__init__(self)
        self._has_focus = False

    def get_focus(self):
        self._has_focus = True
        if self._parentContainer:
            index = self._parentContainer.get_entity_focus_index(self)
            self._parentContainer.set_focus_index(index)
    def lose_focus(self):
        self._has_focus = False

    def has_focus(self) -> bool:
        return self._has_focus

    def trigger(self, parent=None):
        pass

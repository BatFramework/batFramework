import batFramework as bf
from typing import TYPE_CHECKING,Self
import pygame
# if TYPE_CHECKING:
from .cutscene import Cutscene


class CutsceneManager(metaclass=bf.Singleton):
    def __init__(self) -> None:
        self.current_cutscene: Cutscene = None
        self.manager: bf.Manager = None

    def set_manager(self, manager):
        self.manager = manager

    def process_event(self, event):
        if self.current_cutscene is not None:
            self.current_cutscene.process_event(event)
            if event.type in bf.enums.playerInput:
                event.consumed = True

    def play(self,cutscene:Cutscene):
        if self.current_cutscene is not None:return
        self.current_cutscene = cutscene
        cutscene.start()

    def update(self,dt):
        if self.current_cutscene:
            self.current_cutscene.update(dt)
            if self.current_cutscene.is_over:
                self.current_cutscene = None

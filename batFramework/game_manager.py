import pygame

from . import lib as lib
from .scene import Scene
from .scene_manager import SceneManager


class GameManager:
    def __init__(self, resolution : tuple[int], fps : int, *flags : int,font_path:str=None,font_size:int=18):
        pygame.init()
        if font_path :
            lib.set_font(font_path,font_size) 

        pygame.display.set_mode(resolution, *flags)

        self._sceneManager = SceneManager(self)
        self._clock = pygame.time.Clock()
        self._fps = fps
        self.progpagateEvent = False
        self._loop: bool = True

        self.on_init()

    def get_clock(self):
        return self._clock

    def add_scene(self, name: str, scene: Scene):
        self._sceneManager.add_scene(name, scene)

    def on_init(self):  # customize
        pass

    def disable_propagate(self):
        self.progpagateEvent = False

    def _on_event(self, event: pygame.event.Event):
        if event.type == pygame.QUIT or (
            event.type == pygame.KEYDOWN and event.key == pygame.K_F4
        ):
            self._loop = False
            return

        self.on_event(event)
        if self.progpagateEvent:
            self._sceneManager.on_event(event)

    def on_event(self, event):
        pass

    def on_exit(self):
        pass

    def quit(self):
        self.on_exit()
        self._loop = False

    def run(self):
        if self._sceneManager.is_empty():
            raise ValueError
        dtLimit = 40 / 1000
        display = pygame.display.get_surface()
        getTicksLastFrame = pygame.time.get_ticks() - 100
        while self._loop:
            t = pygame.time.get_ticks()

            # deltaTime in seconds.
            dt = (t - getTicksLastFrame) / 1000.0
            getTicksLastFrame = t
            if dt > dtLimit:
                dt = 0.0016
            for event in pygame.event.get():
                self.progpagateEvent = True
                self._on_event(event)

            self._clock.tick(self._fps)
            self._sceneManager.update(dt)
            self._sceneManager.draw(display)

            pygame.display.flip()
        pygame.quit()

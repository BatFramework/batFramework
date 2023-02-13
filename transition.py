from math import sin

import pygame

from batFramework import Color

from .scene import Scene


class Transition(Scene):
    def __init__(self, time=100):
        super().__init__(None, None)

        self._source: Scene = None
        self._dest: Scene = None
        self._timer = time
        self._totalTime = time
        self.set_id(str(id(self)))

    def set_source(self, scene: Scene):
        self._source = scene

    def set_dest(self, scene: Scene):
        self._dest = scene

    def get_progression(self) -> float:
        return 1 - abs(self._timer) / abs(self._totalTime)

    def switch(self):
        self.get_scene_manager().set_scene(self._dest.get_id())
        self.get_scene_manager().remove_scene(self.get_id())

    def update(self, dt: float):
        self._timer -= dt * 60
        if self._timer < 0:
            self._timer = 0
            self.switch()


class FadeColor(Transition):
    def __init__(self, time=100, color=Color.BLACK):
        super().__init__(time)
        self._color = color
        self._surface = pygame.Surface(
            (self._camera.get_surface_rect().size)
        ).convert_alpha()
        self._surface.fill(color)
        self._surface.set_alpha(0)

    def update(self, dt: float):
        super().update(dt)

    def draw(self, surface: pygame.Surface):
        if self.get_progression() < 0.5:
            self._source.draw(surface)
        if self.get_progression() > 0.5:
            self._dest.draw(surface)
        self._surface.set_alpha(255 * sin(self.get_progression() * 3))
        surface.blit(self._surface, (0, 0))


class Vignette(Transition):
    def __init__(self, time=100):
        super().__init__(time)
        self._full_width = self._camera.get_surface_rect().width
        self._surface = pygame.Surface(
            (self._camera.get_surface_rect().size)
        ).convert_alpha()


    def draw(self, surface: pygame.Surface):
        if self.get_progression() < 0.5:
            self._source.draw(surface)
        if self.get_progression() > 0.5:
            self._dest.draw(surface)
        self._surface.set_alpha(255 * sin(self.get_progression() * 3))
        surface.blit(self._surface, (0, 0))
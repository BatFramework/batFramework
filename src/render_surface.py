from math import ceil

import pygame


class RenderSurface:
    def __init__(self, resolution: list[int]) -> None:
        self._baseResolution = resolution
        self._surface = pygame.Surface(resolution).convert_alpha()
        self._surface.fill((0, 0, 0, 0))
        self.surfaceDict = {str(resolution): self._surface}

    def get_surface(self):
        return self._surface

    def set_zoom(self, value: float):
        zoom = 1 / value
        newRes = [self._baseResolution[0] * zoom, self._baseResolution[1] * zoom]
        newResStr = str(newRes)
        if newResStr not in self.surfaceDict.keys():
            self.surfaceDict[newResStr] = pygame.surface.Surface(newRes).convert_alpha()
        self._surface = self.surfaceDict[newResStr]

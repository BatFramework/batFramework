import pygame
from .resourceManager import ResourceManager
import batFramework as bf


class Tileset:
    def __init__(self, source: pygame.Surface | str, tilesize) -> None:
        if isinstance(source, str):
            source = ResourceManager().get_image(source, convert_alpha=True)

        self.surface = source
        self.tile_size = tilesize

        def tile_creator(s) -> pygame.Surface:
            return {
                (False, False): s,
                (False, True): pygame.transform.flip(s, False, True),
                (True, False): pygame.transform.flip(s, True, False),
                (True, True): pygame.transform.flip(s, True, True),
            }

        self.tile_dict = bf.utils.split_surface(
            self.surface, self.tile_size, tile_creator
        )

    def get_tile(self, x, y, flipX=False, flipY=False) -> pygame.Surface | None:
        tile_data = self.tile_dict.get((x, y), None)
        if tile_data is None:
            return None
        return tile_data[(flipX, flipY)]

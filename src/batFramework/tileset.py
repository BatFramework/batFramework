import pygame
from .resourceManager import ResourceManager
import batFramework as bf



class Tileset:
    def __init__(self, source: pygame.Surface, tilesize: tuple[int, int]) -> None:
        self.surface = source
        self.tile_size = tilesize
        self.tile_width = source.get_width() // tilesize[0]
        self.tile_height = source.get_height() // tilesize[1]
        # Create flipped versions of the tileset surface
        self.flipped_surfaces = {
            (False, False): self.surface,
            (False, True): pygame.transform.flip(self.surface, False, True),
            (True, False): pygame.transform.flip(self.surface, True, False),
            (True, True): pygame.transform.flip(self.surface, True, True),
        }

        # Split each of the surfaces into tiles
        self.tile_dict = {}
        for flip_state, surf in self.flipped_surfaces.items():
            tiles = bf.utils.split_surface(surf, self.tile_size)
            for coord, tile in tiles.items():
                if coord not in self.tile_dict:
                    self.tile_dict[coord] = {}
                self.tile_dict[coord][flip_state] = tile


    def __str__(self)->str:
        num_tiles = 0
        if self.tile_dict:
            num_tiles = len(self.tile_dict.values())
        return f"{num_tiles} tiles | Tile size : {self.tile_size}"

    def get_tile(self, x, y, flipX=False, flipY=False) -> pygame.Surface | None:

        if flipX:
            x = self.tile_width - 1 - x
        if flipY:
            y = self.tile_height - 1 - y
        tile_data = self.tile_dict.get((x, y), None)
        if tile_data is None:
            return None
        return tile_data.get((flipX, flipY), None)

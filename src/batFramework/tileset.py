import pygame
from .utils import Utils


class Tileset:
    _tilesets = {}
    _flip_cache = {}  # {"tileset":tileset,"index","flipX","flipY"}

    def __init__(self, source: pygame.Surface | str, tilesize) -> None:
        if isinstance(source, str):
            source = pygame.image.load(Utils.get_path(source)).convert_alpha()

        self.tile_dict = {}
        self.surface = source
        self.tile_size = tilesize
        self.split_surface(self.surface)

    def split_surface(self, surface: pygame.Surface):
        width, height = surface.get_size()
        num_tiles_x = width // self.tile_size
        num_tiles_y = height // self.tile_size
        # Iterate over the tiles vertically and horizontally
        for y in range(num_tiles_y):
            for x in range(num_tiles_x):
                # Calculate the coordinates of the current tile in the tileset
                tile_x = x * self.tile_size
                tile_y = y * self.tile_size
                # Create a subsurface for the current tile
                tile_surface = surface.subsurface(
                    pygame.Rect(tile_x, tile_y, self.tile_size, self.tile_size)
                )
                # Calculate the unique key for the tile (e.g., based on its coordinates)
                tile_key = (x, y)
                # Store the subsurface in the dictionary with the corresponding key
                self.tile_dict[tile_key] = tile_surface
        # print(self.tile_dict)

    def get_tile(self, x, y, flipX=False, flipY=False) -> pygame.Surface | None:
        if (x, y) not in self.tile_dict:
            return None
        if flipX or flipY:
            key = f"{x}{y}:{flipX}{flipY}"
            if not key in self._flip_cache:
                self._flip_cache[key] = pygame.transform.flip(
                    self.tile_dict[(x, y)], flipX, flipY
                )
            return self._flip_cache[key]
        return self.tile_dict[(x, y)]

    @staticmethod
    def load_tileset(path: str, name: str, tilesize) -> "Tileset":
        if name in Tileset._tilesets:
            return Tileset._tilesets[name]
        else:
            img = pygame.image.load(Utils.get_path(path)).convert_alpha()
            tileset = Tileset(img, tilesize)
            Tileset._tilesets[name] = tileset
            return tileset

    @staticmethod
    def get_tileset(name: str) -> "Tileset":
        if name not in Tileset._tilesets:
            return None
        return Tileset._tilesets[name]

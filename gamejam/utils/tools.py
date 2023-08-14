import batFramework as bf
from game_constants import GameConstants as gconst
import random
import pygame
from math import sin

def world_to_grid(x, y):
    return x // gconst.TILE_SIZE, y // gconst.TILE_SIZE


def grid_to_world(x, y):
    return x * gconst.TILE_SIZE, y * gconst.TILE_SIZE


def grid_to_chunk(x, y):
    return x // gconst.CHUNK_SIZE, y // gconst.CHUNK_SIZE


def load_level(level, n: int):
    data = bf.utils.load_json_from_file(f"levels/level_{n}.json")
    if data == None:
        return False
    return level.load(data)


import pygame
import os

#font_path = "data/font.ttf"
BASE_FONT: pygame.font.Font = None
ASSETSCALE = 1

pygame.font.init()
try:
    BASE_FONT = pygame.font.SysFont(name="Corbel",size = 18)
except Exception as e:
    print("Error in init_font:", e)

def set_font(path:str,size:int=18):
    global BASE_FONT
    try:
        BASE_FONT = pygame.font.Font(path,size)
    except Exception as e:
        print("Error in init_font:", e)

def slicer(path, width, height) -> list[pygame.Surface]:
    absPath = os.path.abspath(path)
    surf = pygame.image.load(absPath).convert_alpha()
    cols = surf.get_size()[0] // width
    rows = surf.get_size()[1] // height
    res = []
    for y in range(rows):
        for x in range(cols):
            sub = pygame.Surface.subsurface(
                surf, [x * width, y * height, width, height]
            ).copy()
            if ASSETSCALE != 1:
                res.append(
                    pygame.transform.scale(sub, (width * ASSETSCALE, height * ASSETSCALE))
                )
            else:
                res.append(sub)
    return res

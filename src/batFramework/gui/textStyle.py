from dataclasses import dataclass
import pygame


@dataclass
class TextStyle:
    text: str
    font: pygame.font.Font
    color: any = (0, 0, 0)
    bg_color: any = None
    bold: bool = False
    italic: bool = False
    underline: bool = False
    antialias: bool = False
    wraplength: int = 0
    text_outline_mask: pygame.Mask | None = None
    text_outline_color: pygame.typing.ColorLike = (0, 0, 0)

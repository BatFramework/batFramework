from .utils import Singleton

# put font stuff here later
import pygame
import os
import batFramework as bf


class FontManager(metaclass=Singleton):
    def __init__(self):
        pygame.font.init()
        self.DEFAULT_TEXT_SIZE = 16
        self.MIN_FONT_SIZE = 8
        self.MAX_FONT_SIZE = 64
        self.DEFAULT_ANTIALIAS = False
        self.FONTS = {}

    def set_antialias(self,value:bool):
        self.DEFAULT_ANTIALIAS = value

    def set_default_text_size(self, size: int):
        self.DEFAULT_TEXT_SIZE = size

    def init_font(self, raw_path: str | None):
        try:
            if raw_path is not None:
                self.load_font(raw_path if raw_path else None, None)
            self.load_font(raw_path)
        except FileNotFoundError:
            self.load_sysfont(raw_path)
            self.load_sysfont(raw_path, None)

    def load_font(self, path: str | None, name: str | None = ""):
        if path is not None:
            path = bf.ResourceManager().get_path(path)  # convert path if given
        filename = None
        if path is not None:
            filename = os.path.basename(path).split(".")[0]

        # get filename if path is given, else None
        if name != "":
            filename = name  # if name is not given, name is the filename
        self.FONTS[filename] = {}
        # fill the dict
        for size in range(self.MIN_FONT_SIZE, self.MAX_FONT_SIZE, 2):
            self.FONTS[filename][size] = pygame.font.Font(path, size=size)

    def load_sysfont(self, font_name: str | None, key: str | None = ""):
        if key == "":
            key = font_name
        if font_name is None or pygame.font.match_font(font_name) is None:
            raise FileNotFoundError(f"Requested font '{font_name}' was not found")
        self.FONTS[font_name] = {}

        for size in range(self.MIN_FONT_SIZE, self.MAX_FONT_SIZE, 2):
            self.FONTS[key][size] = pygame.font.SysFont(font_name, size=size)

    def get_font(
        self, name: str | None = None, text_size: int = 12
    ) -> pygame.Font | None:
        if not name in self.FONTS:
            return None
        if not text_size in self.FONTS[name]:
            return None
        return self.FONTS[name][text_size]

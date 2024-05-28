import batFramework as bf
import os
import pygame
import sys
import json
from .utils import Singleton

if getattr(sys, "frozen", False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app
    # path into variable _MEIPASS'.
    application_path = sys._MEIPASS
else:
    application_path = os.getcwd()


class ResourceManager(metaclass=Singleton):
    def __init__(self):
        self.convert_image_cache = {}
        self.convert_alpha_image_cache = {}
        self.sound_cache = {}
        self.RESOURCE_PATH = "."

    def load_dir(self, path) -> None:
        for root, dirs, files in os.walk(path):
            files = [f for f in files if not f[0] == "."]
            dirs[:] = [d for d in dirs if not d[0] == "."]

            for file in files:
                file_path = os.path.join(root, file)
                if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                    self.load_image(file_path)
                    # print(f"Loaded image : '{file_path}'")

                elif file.lower().endswith((".mp3", ".wav")):
                    bf.AudioManager().load_sound(file.lower().split(".")[0], file_path)
                    # print(f"Loaded sound : '{file_path}'")

                elif file.lower().endswith((".ttf", ".otf")):
                    bf.FontManager().load_font(file_path, file.lower().split(".")[0])
                    # print(f"Loaded font : '{file_path}'")

        print(f"Loaded resources in directory : '{path}'")

    def set_resource_path(self, path: str):
        self.RESOURCE_PATH = os.path.join(application_path, path)
        print(f"Resource path : '{self.RESOURCE_PATH}'")

    def get_path(self, path: str) -> str:
        # Normalize path separators
        normalized_path = path.replace("/", os.sep).replace("\\", os.sep)
        return os.path.join(self.RESOURCE_PATH, normalized_path)

    def load_image(self, path) -> None:
        key = self.get_path(path)
        if key in self.convert_image_cache:
            return
        self.convert_image_cache[key] = pygame.image.load(path).convert()
        self.convert_alpha_image_cache[key] = pygame.image.load(path).convert_alpha()

    def get_image(self, path, convert_alpha: bool = False) -> pygame.Surface | None:
        key = self.get_path(path)
        return (
            self.convert_alpha_image_cache.get(key, None)
            if convert_alpha
            else self.convert_image_cache.get(key, None)
        )

    def load_json_from_file(self, path: str) -> dict | None:
        try:
            with open(self.get_path(path), "r") as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            print(f"File '{path}' not found")
            return None

    def save_json_to_file(self, path: str, data) -> bool:
        try:
            with open(self.get_path(path), "w") as file:
                json.dump(data, file, indent=2)
            return True
        except FileNotFoundError:
            return False

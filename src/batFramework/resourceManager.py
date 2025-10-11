import batFramework as bf
import os
import pygame
import sys
import json
from typing import Any, Callable
from .utils import Singleton
import asyncio


if getattr(sys, "frozen", False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app
    # path into variable _MEIPASS'.
    application_path = sys._MEIPASS
else:
    application_path = os.getcwd()


class ResourceManager(metaclass=Singleton):
    def __init__(self):
        self.shared_variables: dict[str, Any] = {}
        self.convert_image_cache = {}
        self.convert_alpha_image_cache = {}
        self.sound_cache = {}
        self.RESOURCE_PATH = "."
        self.loading_thread = None

    def load_resources(self, path: str, progress_callback: Callable[[float], Any] = None):
        """
        loads resources from a directory.
        Progress is reported through the callback.
        Supposed to be asynchronous but don't use it as such yet
        """
        self.progress_callback = progress_callback

        total_files = sum(
            len(files) for _, _, files in os.walk(path) if not any(f.startswith(".") for f in files)
        )

        loaded_files = 0

        for root, dirs, files in os.walk(path):
            files = [f for f in files if not f.startswith(".")]
            dirs[:] = [d for d in dirs if not (d.startswith(".") or d.startswith("__"))]
            for file in files:
                file_path = os.path.join(root, file)

                # Simulate resource loading
                # await asyncio.sleep(0)  # Yield control to the event loop

                if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                    self.load_image(file_path)
                elif file.lower().endswith((".mp3", ".wav", ".ogg")):
                    bf.AudioManager().load_sound(file.split(".")[0], file_path)
                elif file.lower().endswith((".ttf", ".otf")):
                    bf.FontManager().load_font(file_path, file.split(".")[0])

                loaded_files += 1
                # Report progress
                # if self.progress_callback:
                    # self.progress_callback(loaded_files / total_files)

        print(f"Loaded resources in directory: '{path}'")


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


    def set_sharedVar(self, name, value) -> bool:
        """
        Set a shared variable of any type. This will be accessible (read/write) from any scene
        """
        self.shared_variables[name] = value
        return True

    def set_sharedVars(self, variables: dict) -> bool:
        """
        Set multiple shared variables at once. This will be accessible (read/write) from any scene.
        """
        if not isinstance(variables, dict):
            raise ValueError("Input must be a dictionary")
        self.shared_variables.update(variables)
        return True

    def get_sharedVar(self, name, error_value=None):
        """
        Get a shared variable
        """
        return self.shared_variables.get(name, error_value)

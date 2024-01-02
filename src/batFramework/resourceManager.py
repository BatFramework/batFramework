import batFramework as bf
import os
import pygame
import sys
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

    def load_dir(self,path)->None:
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    self.load_image(file_path)
                elif file.lower().endswith(('.mp3', '.wav')):
                    self.load_sound(file_path)

    def set_resource_path(self,path: str):
        self.RESOURCE_PATH = os.path.join(application_path, path)
        print(f"set resource path to '{self.RESOURCE_PATH}'")
        

    def get_path(self,path: str):
        return os.path.join(self.RESOURCE_PATH, path)
        
    def load_image(self,path)->None:
        key = self.get_path(path)
        if key in self.convert_image_cache : return
        self.convert_image_cache[key] = pygame.image.load(path).convert()
        self.convert_alpha_image_cache[key] = pygame.image.load(path).convert_alpha()
        
    def load_sound(self,path)->None:
        pass
        
    def get_image(self,path,convert_alpha:bool=False):   
        key = self.get_path(path)
        return self.convert_alpha_image_cache.get(key,None) if\
         convert_alpha else self.convert_image_cache.get(key,None)
    
    def get_sound(self,path):
        return None


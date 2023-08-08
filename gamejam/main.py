#WINDOW AND INITIALIZATION STUFF

import sys
import os
os.environ['SDL_VIDEO_CENTERED'] = '1'
# Get the path to the parent directory of batFramework
batframework_parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# Add the parent directory to sys.path
sys.path.insert(0, batframework_parent_dir)


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS

        base_path = sys._MEIPASS
        # print("BASE PATH ->",base_path)
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

import pygame
from myManager import MyManager 

def main():
    pygame.init()
    pygame.display.set_caption("GAME")
    MyManager.set_resource_path(resource_path("gamejam/data"))
    m = MyManager()
    # pygame.display.toggle_fullscreen()
    m.run()


if __name__ == "__main__":
    main()
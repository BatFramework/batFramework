import sys
import os

# Get the path to the parent directory of batFramework
batframework_parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add the parent directory to sys.path
sys.path.insert(0, batframework_parent_dir)

import pygame
from myManager import MyManager




if __name__ == "__main__":
    pygame.init()
    path = pygame.system.get_pref_path("bat", "game")
    print(path)
    # print(sys.path)
    m = MyManager()
    # import cProfile, pstats
    # profiler = cProfile.Profile()
    # profiler.enable()
    m.run()
    # profiler.disable()
    # stats = pstats.Stats(profiler).sort_stats('tottime')
    # stats.print_stats()


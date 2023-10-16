import os
import sys
import pygame
os.environ["SDL_VIDEO_CENTERED"] = "1"

batframework_parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, batframework_parent_dir)
from batFramework import init

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
        base_path = os.path.join(os.
        path.abspath(__file__),os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)

    pygame.display.set_caption("GAME")
    # Import batframework after modifying sys.path
    from batFramework import init

    init(
        (160,144),
        pygame.SCALED,
        default_text_size=8,
        resource_path=resource_path("data"),
        default_font="fonts/slkscr.ttf",
        window_title="Tied Together"
    )



    from myManager import MyManager
    m = MyManager()
    m.run()

if __name__ == "__main__":
    setup_framework()

import batFramework as bf
from titleScene import TitleScene
from mainScene import MainScene
from optionScene import OptionScene
from editorScene import EditorScene
from level import Level
import pygame
from pathlib import Path
from os.path import join

class MyManager(bf.Manager):
    def __init__(self) -> None:
        self.set_resource_path(join(Path(__file__).parent,"data"))
        title = TitleScene()
        super().__init__((320,180),"Dahlia",[title])

    def do_init(self):
        self.set_sharedVar("is_debugging_func",False)
        self.set_sharedVar("totalBlitCalls",0)
        level = Level()
        self.set_sharedVar("level",level)
        main = MainScene()
        editor = EditorScene()
        opt = OptionScene()
        self.add_scene(main)
        self.add_scene(editor)
        self.add_scene(opt)
        self.set_scene("title")

    def process_event(self, event: pygame.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.print_status()
        super().process_event(event)

import batFramework as bf

# import os
# from pathlib import Path
from utils.defaults import Defaults
from scenes import *
# from game_constants  import GameConstants as  gconst


class MyManager(bf.Manager):
    def __init__(self) -> None:
        Defaults.initialize()
        # super().__init__(BootScene(),TitleScene(),OptionsScene(),EditorScene(),TilePicker(),GameScene(),DialogueScene()) # with boot
        super().__init__(
            TitleScene(),
            OptionsScene(),
            EditorScene(),
            TilePickerScene(),
            GameScene(),
            DialogueScene(),
            MovieScene()
        )

import batFramework as bf
import os
from pathlib import Path
from utils.defaults import Defaults
from titleScene import TitleScene
from gameScene import GameScene
from optionsScene import OptionsScene
from bootScene import BootScene
from tilePicker import TilePicker
from editorScene import EditorScene
from dialogueScene import DialogueScene
from game_constants  import GameConstants as  gconst

class MyManager(bf.Manager):
    def __init__(self) -> None:
        Defaults.initialize()
        super().__init__(BootScene(),TitleScene(),OptionsScene(),EditorScene(),TilePicker(),GameScene(),DialogueScene()) # with boot
        # super().__init__(TitleScene(),OptionsScene(),GameScene(),EditorScene(),TilePicker())


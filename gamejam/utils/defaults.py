import batFramework as bf
from game_constants import GameConstants as gconst
class Defaults:
    @staticmethod
    def initialize():
        #load sounds
        bf.AudioManager().load_music("level","audio/music/level.wav")
        bf.AudioManager().load_sound("click","audio/sfx/click.wav",True)
        bf.AudioManager().load_sound("switch","audio/sfx/switch.wav",True)
        bf.AudioManager().load_sound("click_fade","audio/sfx/click_fade.wav",True)
        bf.AudioManager().load_sound("text_click","audio/sfx/text_click.wav",True)
        bf.AudioManager().load_sound("step","audio/sfx/step.wav",True)
        bf.AudioManager().load_sound("jump","audio/sfx/jump.wav",True)
        bf.AudioManager().load_sound("pick_up","audio/sfx/pick_up.wav",True)

        #Load tileset 
        bf.utils.load_tileset("tilesets/tileset.png","tileset",gconst.TILE_SIZE)

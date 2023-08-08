import batFramework as bf
import pygame
from custom_scenes import CustomBaseScene
from level import Level
import utils.tools as tools
from player import Player
from baby import Baby
import random
class GameScene(CustomBaseScene):
    def __init__(self) -> None:
        super().__init__("game")

        self.add_action(
            bf.Action("left").add_key_control(pygame.K_LEFT).set_holding(),
            bf.Action("right").add_key_control(pygame.K_RIGHT).set_holding(),
            bf.Action("up").add_key_control(pygame.K_UP).set_holding(),
            bf.Action("down").add_key_control(pygame.K_DOWN).set_holding(),
            bf.Action("options").add_key_control(pygame.K_ESCAPE),
            bf.Action("spawn").add_key_control(pygame.K_0),
            bf.Action("editor").add_key_control(pygame.K_e),
            bf.Action("cutscene").add_key_control(pygame.K_c)

            )

        self.pm = bf.ParticleManager()
        self.add_world_entity(self.pm)

    def do_when_added(self):
        self.debugger = bf.Debugger(self.manager).set_outline(False).set_text_color(bf.color.BASE_GB)
        self.add_hud_entity(self.debugger)
        
        self.level :Level= Level()
        self.add_world_entity(self.level)
        self.set_sharedVar("level",self.level)
        tools.load_level(self.level,0)

        self.player : Player = Player()
        self.baby = Baby()
        spawn_point = (100,20)
        self.player.spawn_point = spawn_point
        self.baby.spawn_point = spawn_point

        bf.Time().timer(
            "particle",100,
            True,lambda : self.pm.add_particle((random.randrange(self.player.rect.center))) if self.is_active() else 0)

        self.set_sharedVar("player",self.player)
        self.set_sharedVar("baby",self.baby)
        self.add_world_entity(self.player,self.baby)



        self.set_sharedVar("game_camera",self.camera)
        self.spawn()

    def on_enter(self):
        self.camera.set_follow_dynamic_point(lambda : self.player.rect.move(0,-10).center)
        # self._action_container.hard_reset()
        self.player.action_container.hard_reset()

    def spawn(self):
        self.player.set_position(*self.player.spawn_point)
        self.baby.set_position(*self.baby.spawn_point)


    def do_early_process_event(self, event) -> bool:
        if self.get_sharedVar("in_cutscene"):
            return True
        return False

    def do_handle_event(self, event):
        if self._action_container.is_active("options"):
            self.manager.transition_to_scene("options",bf.FadeTransition)
        if self._action_container.is_active("editor"):
            self.manager.set_scene("editor")
        if self._action_container.is_active("spawn"):
            self.spawn()
        if self._action_container.is_active("cutscene"):
            pass
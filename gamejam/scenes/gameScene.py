import batFramework as bf
import pygame
from .custom_scenes import CustomBaseScene
from level import Level, Tile
import utils.tools as tools
from player import Player
from baby import Baby
import random
from game_constants import GameConstants as gconst


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
            bf.Action("switch_player").add_key_control(pygame.K_y),
            bf.Action("warp").add_key_control(pygame.K_v),
        )

        self.switch_tries = 0
        self.switch_indicators = []

        self.pm = bf.ParticleManager()
        self.add_world_entity(self.pm)
        def bubble_maker(color):
            self.pm.add_particle(
            start_pos=(
                random.randrange(
                int(self.camera.rect.left) - 100,
                int(self.camera.rect.right) + 100,
                ),self.camera.rect.bottom + random.randint(0, 20)),
            start_vel=(0, -6 * random.random() * 4),
            color=color,duration=8000)
        def generate_particles():
            for _ in range(2):
                bubble_maker(bf.color.LIGHT_GB)
                bubble_maker(bf.color.SHADE_GB)

        self.particle_timer = bf.Timer(
            name="bubbles",duration=300,loop=True,
            end_callback=generate_particles
        )

    def do_when_added(self):
        self.debugger = (
            bf.Debugger(self.manager)
            .set_outline(False)
            .set_text_color(bf.color.BASE_GB)
        )
        self.debugger.add_dynamic_data(
            "player", lambda: self.get_sharedVar("current_player")
        )
        self.add_hud_entity(self.debugger)

        self.level: Level = Level()
        self.add_world_entity(self.level)
        self.set_sharedVar("level", self.level)
        tools.load_level(self.level, 0)

        self.player: Player = Player()
        self.baby = Baby()

        spawn_point = (100, 20)

        self.player.spawn_point = spawn_point
        self.baby.spawn_point = spawn_point

        self.player_follow_func = lambda: self.player.rect.move(0, -10).center
        self.baby_follow_func = lambda: self.baby.rect.move(0, -10).center


        self.set_sharedVar("player", self.player)
        self.set_sharedVar("baby", self.baby)
        self.set_sharedVar("current_player", "player")
        self.add_world_entity(self.player, self.baby)

        self.set_sharedVar("game_camera", self.camera)
        self.spawn()




    def on_enter(self):
        super().on_enter()
        self.camera.set_follow_dynamic_point(
            self.player_follow_func if self.player.control else self.baby_follow_func
        )
        self.camera.set_center(*self.camera.follow_point_func())
        self.player.action_container.hard_reset()
        self.particle_timer.start()

    def on_exit(self):
        super().on_exit()
        self.particle_timer.stop()

    def add_switch(self):
        self.switch_indicators.append(
            Tile(
                2 + self.switch_tries * (gconst.TILE_SIZE + 2),
                gconst.TILE_SIZE - 2,
                (1, 1),
                tags=["wave"],
            )
        )
        self.switch_tries += 1
        self.add_hud_entity(self.switch_indicators[-1])

    def remove_switch(self):
        self.switch_tries -= 1
        self.remove_hud_entity(self.switch_indicators[-1])
        self.switch_indicators.pop(-1)

    def spawn(self):
        if self.get_sharedVar("current_player") != "player":
            self.switch_players()
        tools.load_level(self.level, 0)

        self.player.set_position(*self.player.spawn_point)
        self.baby.set_position(*self.baby.spawn_point)
        self.switch_tries = 0
        for ind in self.switch_indicators:
            self.remove_hud_entity(ind)
        self.switch_indicators = []
        for _ in range(3):
            self.add_switch()

    def switch_players(self):
        current_player = self.get_sharedVar("current_player")
        if current_player == "player":
            self.baby.hold(False)
            self.baby.set_control(True)
            self.player.set_control(False)
            self.camera.set_follow_dynamic_point(self.player_follow_func if self.player.control else self.baby_follow_func)
            self.set_sharedVar("current_player", "baby")
        else:
            self.baby.set_control(False)
            self.player.set_control(True)
            self.camera.set_follow_dynamic_point(self.player_follow_func if self.player.control else self.baby_follow_func)
            self.set_sharedVar("current_player", "player")



    def do_handle_event(self, event):
        if self.actions.is_active("options"):
            self.manager.transition_to_scene("options", bf.FadeTransition)
        if self.actions.is_active("editor"):
            self.manager.set_scene("editor")
        if self.actions.is_active("spawn"):
            self.spawn()
        if self.actions.is_active("switch_player"):
            if self.switch_tries <= 0:
                return
            self.remove_switch()
            self.switch_players()
        if self.actions.is_active("warp"):
            self.player.warp()

    def do_update(self, dt):
        pkillers: list[bf.Entity] = self.level.get_by_tag("pKill")
        if self.player.rect.collideobjects(pkillers, key=lambda p: p.rect):
            self.spawn()
            return
        Akillers: list[bf.Entity] = self.level.get_by_tag("AKill")
        if self.player.rect.collideobjects(
            Akillers, key=lambda p: p.rect
        ) or self.baby.rect.collideobjects(Akillers, key=lambda p: p.rect):
            self.spawn()
        switch_add: list[bf.Entity] = self.level.get_by_tag("+switch")
        obj = self.player.rect.collideobjects(
            switch_add, key=lambda p: p.rect
        ) or self.baby.rect.collideobjects(Akillers, key=lambda p: p.rect)
        if obj:
            self.add_switch()
            bf.AudioManager().play_sound("switch")
            self.level.remove_entity(obj)

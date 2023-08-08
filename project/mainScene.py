import batFramework as bf
import pygame
from player import Player
from level import Level, grid_to_world,world_to_grid
class MainScene(bf.Scene):
    def __init__(self):
        super().__init__("main")
        self.set_clear_color((70,70,70))
    def on_exit(self):
        self.player.action_container.hard_reset()

    def do_when_added(self):
        self.level: Level = self.get_sharedVar("level")
        self.set_sharedVar("mainCamera", self.camera)
        self.add_world_entity(self.level)
        self.level.set_background_image("background/sky.png")

        self.player = Player()
        self.player.spawn_point = grid_to_world(5,6)
        self.add_world_entity(self.player)

        self._action_container.add_action(bf.Action("fullscreen").add_key_control(pygame.K_F4))
        self._action_container.add_action(bf.Action("options").add_key_control(pygame.K_ESCAPE))
        self._action_container.add_action(bf.Action("editor").add_key_control(pygame.K_e))
        self._action_container.add_action(bf.Action("minus_zoom").add_key_control(pygame.K_n))
        self._action_container.add_action(bf.Action("plus_zoom").add_key_control(pygame.K_m))
        self._action_container.add_action(bf.Action("spawn").add_key_control(pygame.K_1))

        self.debugger = bf.Debugger(self.manager)
        # self.debugger.set_refresh_rate(1)
        self.add_hud_entity(self.debugger)

        self.debugger.add_dynamic_data("Chunks", lambda: str(self.level.get_data()[0]))
        self.debugger.add_dynamic_data("Tiles", lambda: str(self.level.get_data()[1]))
        self.debugger.add_dynamic_data("Grid",
                                lambda: world_to_grid(*[int(i) for i in
                                                        self.camera.convert_screen_to_world(*pygame.mouse.get_pos())]))
        self.debugger.add_dynamic_data("Zoom", lambda: str(round(1 / self.camera.zoom_factor, 2)))
        self.debugger.add_dynamic_data("Pos", lambda: str(pygame.Rect(self.player.rect).center))
        self.debugger.add_dynamic_data("Cam", lambda: [round(i, 2) for i in self.camera.rect.center])
        self.debugger.add_dynamic_data("Vel", lambda: str(self.player.velocity))
        self.debugger.add_dynamic_data("State", lambda: str(self.player.current_animState))
        self.debugger.add_dynamic_data("On_Gnd", lambda: str(self.player.on_ground))
        self.debugger.add_dynamic_data("Frame", lambda: str(self.player.get_frame_index()))

    def on_enter(self):
        self.camera.set_follow_dynamic_point(lambda: self.player.rect.move(0,-self.camera.rect.h //4).center)

    def do_handle_event(self, event):
        if self._action_container.is_active("fullscreen"):
            pygame.display.toggle_fullscreen()
        if self._action_container.is_active("options"):
            self.manager.set_scene("options")
        if self._action_container.is_active("editor"):
            self.manager.set_scene("editor")
        if self._action_container.is_active("minus_zoom"):
            self.camera.zoom(self.camera.zoom_factor + 0.25 )
        if self._action_container.is_active("plus_zoom"):
            self.camera.zoom(self.camera.zoom_factor - 0.25 )
        if self._action_container.is_active("spawn"):
            self.player.set_position(*self.player.spawn_point)
        self._action_container.reset()

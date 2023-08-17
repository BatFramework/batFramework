import batFramework as bf
from .custom_scenes import CustomBaseScene
import pygame
from game_constants import GameConstants as gconst


class OptionsScene(CustomBaseScene):
    def __init__(self) -> None:
        super().__init__("options")

        self.add_hud_entity(bf.Label("OPTIONS"))
        self.set_clear_color(bf.color.DARK_GB)

        self.main_frame = bf.Container("options_main", bf.Layout.FILL)
        self.add_hud_entity(self.main_frame)

        self.btn_music = bf.Button(
            "",
            callback=lambda: self.set_music_volume(
                self.cycle_volume(bf.AudioManager().music_volume)
            ),
        ).put_to(self.main_frame)

        self.btn_sfx = bf.Button(
            "",
            callback=lambda: self.set_sfx_volume(
                self.cycle_volume(bf.AudioManager().sound_volume)
            ),
        ).put_to(self.main_frame)

        bf.Toggle(
            "FULLSCREEN",
            callback=lambda x: pygame.display.toggle_fullscreen(),
            default_value=(
                pygame.display.get_surface().get_flags() & pygame.FULLSCREEN
            ),
        ).put_to(self.main_frame)

        control_button = bf.Button("CONTROLS").put_to(self.main_frame)

        # control_button = bf.Button("FULLSCREENNN").put_to(self.main_frame)

        bf.Button(
            "MAIN MENU",
            callback=lambda: self.manager.transition_to_scene(
                "title", bf.FadeTransition
            ),
        ).put_to(self.main_frame)

        self.btn_resume_game = bf.Button(
            "RESUME",
            callback=lambda: self.manager.transition_to_scene(
                "game", bf.FadeTransition
            ),
        )

        self.main_frame.set_center(*self.hud_camera.rect.center)
        self.set_sfx_volume(gconst.DEFAULT_SFX_VOLUME)
        self.set_music_volume(gconst.DEFAULT_MUSIC_VOLUME)
        self.add_action(bf.Action("resume_key").add_key_control(pygame.K_ESCAPE))

        control_frame = bf.Container("controls")
        self.add_hud_entity(control_frame)
        control_frame.set_visible(False)
        bf.Label("CONTROLS").put_to(control_frame)
        control_back = bf.Button("BACK").put_to(control_frame)
        bf.Label("MOVE:WASD|ARR.KEYS").put_to(control_frame)
        bf.Label("SWITCH:Y").put_to(control_frame)
        bf.Label("NEXT:RETURN|SPACE").put_to(control_frame)


        # control_frame.set_padding((2,2)).set_border_width(0)
        # control_frame.update_content()
        control_frame.set_center(*self.hud_camera.rect.center)

        control_button.set_callback(
            bf.Container.create_link(self.main_frame, control_frame, True)
        )
        control_back.set_callback(
            bf.Container.create_link(control_frame, self.main_frame, True, False)
        )

    def snap_value(self, volume):
        return min(list(gconst.VOLUME_TABLE.values()), key=lambda x: abs(x - volume))

    def cycle_volume(self, volume):
        volumes = list(gconst.VOLUME_TABLE.values())
        if volume not in volumes:
            volume = self.snap_value(volume)
        index = (volumes.index(volume) + 1) % len(volumes)
        return volumes[index]

    def set_sfx_volume(self, volume):
        volume = self.snap_value(volume)
        keys = list(gconst.VOLUME_TABLE.keys())
        values = list(gconst.VOLUME_TABLE.values())

        position = values.index(volume)
        text = keys[position]
        self.btn_sfx.set_text(f"SFX:{text}")
        bf.AudioManager().set_sound_volume(volume)

    def set_music_volume(self, volume):
        volume = self.snap_value(volume)
        keys = list(gconst.VOLUME_TABLE.keys())
        values = list(gconst.VOLUME_TABLE.values())
        position = values.index(volume)
        text = keys[position]
        self.btn_music.set_text(f"MUSIC:{text}")
        bf.AudioManager().set_music_volume(volume)

    def on_enter(self):
        self.main_frame.get_focus()
        if (
            self.manager._scenes[1]._name == "game"
            and not self.btn_resume_game.parent_container
        ):
            self.btn_resume_game.put_to(self.main_frame)
        elif (
            self.manager._scenes[1]._name != "game"
            and self.btn_resume_game.parent_container
        ):
            self.main_frame.remove_entity(self.btn_resume_game)
        # self.manager.print_status()

    def do_when_added(self):
        self.debugger = (
            bf.Debugger(self.manager)
            .set_outline(False)
            .set_text_color(bf.color.BASE_GB)
        )
        self.add_hud_entity(self.debugger)

    def do_handle_event(self, event):
        if self.btn_resume_game.parent_container and self._action_container.is_active(
            "resume_key"
        ):
            self.btn_resume_game.activate(True)

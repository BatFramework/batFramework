import pygame
import batFramework as bf
from custom_scenes import CustomBaseScene

class BootScene(CustomBaseScene):
    def __init__(self) -> None:
        super().__init__("boot")
        self.set_clear_color(bf.color.BASE_GB)
        self.timer = bf.Time().timer(
            name="boot_timer", 
            duration=2000,
            callback=lambda: self.manager.transition_to_scene(
                "title",
                bf.FadeColorTransition,
                duration=2000,
                color_duration=1000,
                color=bf.color.LIGHT_GB
            )
        )
        self.add_action(bf.Action("skip").add_key_control(pygame.K_RETURN,pygame.K_ESCAPE,pygame.K_SPACE))
        self.anim = bf.EasingAnimationManager().create_animation(
            bf.Easing.EASE_IN, 2000, end_callback=self.timer.start)
        lb_boot = bf.Label("Pygame Summer Jam").set_center(*self.hud_camera.rect.center)
        self.add_hud_entity(lb_boot)
        self.color_surf = pygame.Surface(self.hud_camera.rect.size).convert_alpha()
        self.color_surf.fill("black")

    def on_enter(self):
        self.anim.start()
        bf.AudioManager().load_sound("boot", "audio/sfx/boot.wav")
        bf.AudioManager().play_sound("boot")

    def do_final_draw(self, surface):
        self.color_surf.set_alpha(255 - int(255 * self.anim.progression))
        surface.blit(self.color_surf, (0, 0))

    def do_handle_event(self, event ):
        if self._action_container.is_active("skip"):
            self.anim.stop()
            self.timer.stop()
            bf.AudioManager().stop_sound("boot")
            self.manager.transition_to_scene("title",bf.FadeTransition)


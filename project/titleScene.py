import batFramework as bf
import pygame

class TitleScene(bf.Scene):
    def __init__(self) -> None:
        super().__init__("title")
        self.set_clear_color("gray15")
    def do_when_added(self):

        self.buttons = bf.Container()
        self.buttons.set_size(200,300)
        title = bf.Image("icon&text/title.png").set_center(*self.hud_camera.rect.move(0,-self.hud_camera.rect.h//3).center)
        self.add_hud_entity(title)

        bf.Button("PLAY"   ,18,lambda:self.manager.transition_to_scene("main",bf.FadeTransition)).put_to(self.buttons)
        bf.Button("OPTIONS",18,lambda:self.manager.transition_to_scene("options",bf.FadeTransition)).put_to(self.buttons)
        bf.Button("QUIT"   ,18,lambda: pygame.event.post(pygame.Event(pygame.QUIT))).put_to(self.buttons)

        self.buttons.set_center(self.hud_camera.rect.w//2,self.hud_camera.rect.bottom -self.hud_camera.rect.h//3)
        self.add_hud_entity(self.buttons)
        self.buttons.get_focus()
        self.add_hud_entity(bf.Debugger(self.manager))

    def on_enter(self):
        self.camera.set_follow_dynamic_point(None)

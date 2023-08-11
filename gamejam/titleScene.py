
import pygame
import batFramework as bf
from custom_scenes import CustomBaseScene
import cutscenes
class TitleScene(CustomBaseScene):
    def __init__(self) -> None:
        super().__init__("title")
        self.debugger = None



    def do_when_added(self):

        bf.AudioManager().load_music("title_theme","audio/music/main_theme.wav")
        self.music_timer = bf.Time().timer(duration=600,callback=lambda :[bf.AudioManager().play_music("title_theme",-1,0) if bf.AudioManager().current_music != "title_theme" else 0])

        #set up debugger
        self.debugger = bf.Debugger(self.manager).set_outline(False).set_text_color(bf.color.BASE_GB)
        self.debugger.set_background_color(bf.color.DARK_GB)
        self.add_hud_entity(self.debugger)

        #background image
        self.bg1 = bf.Image("backgrounds/ruins.png",True)
        self.bg2 = bf.Image("backgrounds/ruins.png",True)
        self.bg2.set_debug_color(bf.color.ORANGE)
        self.bg2.set_position(self.bg1.rect.left - self.bg2.rect.w,0)
        self.bg_offset = 0

        
        self.add_world_entity(bf.Image("backgrounds/sky.png"),self.bg1,self.bg2)


        title_image= bf.Image("backgrounds/title.png").set_center(*self.hud_camera.rect.move(0,-bf.const.RESOLUTION[1]//4).center)
        self.add_hud_entity(title_image)
        




        bottom_text = bf.Label("Baturay Turan").set_text_color(bf.color.LIGHT_GB).set_outline_color(bf.color.BASE_GB)
        bottom_text.set_position(0,bf.const.RESOLUTION[1]-bottom_text.rect.h)
        self.add_hud_entity(bottom_text)
        bottom_text.set_background_color(None).set_text_color(bf.color.BASE_GB)




        main_frame = bf.Container("title_main")
        self.add_hud_entity(main_frame)

        bf.Button("PLAY",callback=lambda:bf.CutsceneManager().play(cutscenes.IntroCutscene())).put_to(main_frame)
        bf.Button("SHORTCUT",callback=lambda:self.manager.transition_to_scene("game",bf.FadeTransition)).put_to(main_frame)

        bf.Button("OPTIONS",callback=lambda:self.manager.transition_to_scene("options",bf.FadeTransition)).put_to(main_frame)
        bf.Button("QUIT",callback=lambda:pygame.event.post(pygame.Event(pygame.QUIT))).put_to(main_frame)

        # main_frame.update_content()

        tmp = main_frame.rect.copy()
        tmp.midtop = title_image.rect.move(0,4).midbottom
        main_frame.set_center(*tmp.center)
        
        main_frame.get_focus()

    def on_enter(self):
        self.music_timer.start()

    def on_exit(self):
        self.music_timer.stop()

    def do_update(self, dt):
        self.bg_offset +=20 * dt
        self.bg_offset = self.bg_offset % self.bg1.rect.w
        self.bg1.set_position(self.bg_offset,0)
        self.bg2.set_position(self.bg1.rect.left - self.bg2.rect.w,0)
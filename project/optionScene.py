import batFramework as bf
import pygame
from math import cos
def stylize(e : bf.Entity):
    if bf.const.GUI_SCALE != 1 : e.set_size(*e.rect.inflate(e.rect.w//2,e.rect.h//2).size)
    match e:
        case bf.TitledFrame():
            e.set_border_color(bf.color.WET_BLUE).set_border_width(2).set_background_color(bf.color.DARK_BLUE).set_border_radius(10)
            e.title_label.set_background_color(bf.color.WET_BLUE).set_border_radius([0,10,10,0])
        case bf.Button():
            e.set_border_color(bf.color.WET_BLUE).set_background_color(bf.color.WET_BLUE).set_border_radius(10)
        case bf.Container():
            e.set_border_width(2).set_border_color(bf.color.WET_BLUE).set_border_radius(10).set_padding((8,6))
            [stylize(child) for child in e.children]
        case _:return


class TestEntity(bf.Entity):
    def __init__(self,x,y,easing :bf.Easing) -> None:
        super().__init__(size=(8,8))
        self.surface.fill("orange")
        self.set_position(x,y)
        self.anim = bf.EasingAnimationManager().create_animation(easing, 2000, loop=True,update_callback=lambda val :self.set_position(x+val*100,y))
        self.anim.start()

class OptionScene(bf.Scene):
    def __init__(self) -> None:
        super().__init__("options")
        self.camera.set_clear_color("gray20")

    def do_when_added(self):

        self.last_change = 0
        self.cumul = 0


        # INIT GUI
        main_frame = bf.TitledFrame("OPTIONS",size=self.hud_camera.rect.inflate(-20,-20).size).set_position(10,10)
        self.main_container = bf.Container().set_position(*main_frame.title_label.rect.move(10,10).bottomleft)#.set_alignment(bf.Alignment.CENTER)


        self.btn_return = bf.Button("",callback=lambda : self.manager.transition_to_scene(self.manager._scenes[1].get_name(),bf.FadeTransition)).put_to(self.main_container)
        bf.Button("VIDEO").put_to(self.main_container)
        bf.Button("AUDIO").put_to(self.main_container)

        
        self.main_container.get_focus()

        self.add_hud_entity(main_frame,self.main_container)


        test = bf.Container().set_position(main_frame.rect.centerx,main_frame.rect.top + 20).set_alignment(bf.Alignment.LEFT)
        self.btn_test = [
        bf.Panel((50,15)).set_background_color(bf.color.LIGHT_BLUE).set_border_radius(10).put_to(test),
        bf.Panel((50,15)).set_background_color(bf.color.LIGHT_BLUE).set_border_radius(10).put_to(test),
        bf.Panel((50,15)).set_background_color(bf.color.LIGHT_BLUE).set_border_radius(10).put_to(test)
        ]



        self.add_hud_entity(test)
        y = 100
        self.add_hud_entity(TestEntity(main_frame.rect.left,y,bf.Easing.EASE_IN))
        self.add_hud_entity(TestEntity(main_frame.rect.left,y+20,bf.Easing.EASE_OUT))
        self.add_hud_entity(TestEntity(main_frame.rect.left,y+40,bf.Easing.EASE_IN_OUT))


        self.debugger = bf.Debugger(self.manager)
        self.debugger.set_background_color(bf.color.DARK_GRAY)
        self.add_hud_entity(self.debugger)

    def add_hud_entity(self, *entity: bf.Entity):
        super().add_hud_entity(*entity)
        for e in entity:
            stylize(e)

    def on_enter(self):
        if self.manager._scenes[1].get_name() == "title":
            print(self.btn_return.rect.w)

            self.btn_return.set_text("Back to Title")
            print(self.btn_return.rect.w)

        else:
            self.btn_return.set_text("Back")

        self.main_container.update_content()

    def do_update(self, dt):
        self.cumul += dt * 60
        if self.cumul > 2:
            for i,b in enumerate(self.btn_test):
            self.last_change = pygame.time.get_ticks()
            self.cumul = 0
        

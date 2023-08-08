import batFramework as bf
from custom_scenes import CustomBaseScene
from game_constants import GameConstants as gconst
import pygame
import itertools


def set_pos_picker(x,y,picker,shared_var,offset) :
    bf.Entity.set_position(picker,x,y)
    x_index = (x- offset[0]) //8
    y_index = (y- offset[1])//8
    # print(x,y,x_index,y_index)
    shared_var.set_index(x_index,y_index)
    return picker

class TilePicker(CustomBaseScene):
    def __init__(self) -> None:
        super().__init__("tile_picker")
        # self.set_clear_color("white")
        self.bg1 = bf.Image("backgrounds/tile_picker_bg.png",True)
        self.bg2 = bf.Image("backgrounds/tile_picker_bg.png",True)
        self.bg2.set_debug_color(bf.color.ORANGE)
        self.bg2.set_position(self.bg1.rect.left - self.bg2.rect.w,0)
        self.add_hud_entity(self.bg1,self.bg2)
        self.offset  = 0

        self.tileset =bf.utils.get_tileset("tileset")
        self.tileset_image = bf.Image(bf.utils.get_path("tilesets/tileset.png"),True)
        self.tileset_image.set_position(self.hud_camera.rect.right-self.tileset_image.rect.w,0)
        self.add_hud_entity(self.tileset_image)
        self.add_hud_entity(bf.Label("TILE PICKER").set_center(*self.hud_camera.rect.move(0,-10).midbottom))
        self.picker = bf.Entity((gconst.TILE_SIZE,gconst.TILE_SIZE),convert_alpha=True)
        self.picker.set_position = lambda x,y,picker=self.picker: set_pos_picker(x,y,picker,self.get_sharedVar("brush_tile"),self.tileset_image.rect.topleft)
        self.picker.surface.fill((0,0,0,0))



        # s = pygame.Surface(self.hud_camera.rect.size).convert_alpha()
        # line_width = 4
        # line_delta = 80
        # for x in range(-line_width-line_delta,int(self.hud_camera.rect.w+line_width+line_delta),line_width*2):
        #     pygame.draw.line(s,bf.color.DARK_GB,(x,0),(x+line_delta,int(self.hud_camera.rect.h)),line_width)
        # pygame.image.save(s,bf.utils.get_path("backgrounds/tile_picker_bg.png"),"png")

        self.add_action(
            bf.Action("l_click").add_mouse_control(1),bf.Action("resume").add_key_control(pygame.K_ESCAPE,pygame.K_q),
            bf.Action("left").add_key_control(pygame.K_LEFT,pygame.K_a),
            bf.Action("right").add_key_control(pygame.K_RIGHT,pygame.K_d),
            bf.Action("up").add_key_control(pygame.K_UP,pygame.K_w),
            bf.Action("down").add_key_control(pygame.K_DOWN,pygame.K_s)
        )



        colors = [bf.color.DARK_GB,bf.color.SHADE_GB,bf.color.BASE_GB,bf.color.LIGHT_GB]
        incrementer = (i for i in itertools.count())
        incrementer2 = (i for i in itertools.count())
        self.timer1 = bf.Time().timer(
            "change_tile_picker_bg_color",
            500,True,
            lambda : self.set_clear_color(colors[1+next(incrementer)%2])
        )

        self.timer2 = bf.Time().timer(
            "change_picker_color",
            100,True,
            lambda : pygame.draw.rect(self.picker.surface,(colors[(next(incrementer2)%len(colors))]),(0,0,*self.picker.rect.size),1) 
        )

        self.add_hud_entity(self.picker)


        #TAGS SELECTION

        self.tag_container = bf.Container("tag_container")
        bf.Label("TAGS").put_to(self.tag_container)
        for tag in gconst.TAGS:

            bf.Toggle(tag,callback=lambda x,tag_name=tag: self.get_sharedVar("brush_tile").add_tag(tag_name) if x else self.get_sharedVar("brush_tile").remove_tag(tag_name) ).put_to(self.tag_container)

        self.add_hud_entity(self.tag_container)
        self.tag_container.set_padding((10,0)).set_border_width(None).set_background_color(None)
        self.tag_container.resize(self.hud_camera.rect.w-self.tileset_image.rect.w,120)
        self.tag_container.get_focus()

    def cycle_picker_color_index(self):
        colors = [bf.color.BASE_GB,bf.color.LIGHT_GB,bf.color.DARK_GB,bf.color.SHADE_GB]
        self.picker_color_index = (self.picker_color_index +1) % len(colors)
        pygame.draw.rect(self.picker.surface,colors[self.picker_color_index],(0,0,*self.picker.rect.size),1)

    def on_enter(self):
        self.picker.set_position(*self.tileset_image.rect.move(*[i * 8 for i in self.get_sharedVar("brush_tile").tile_index]).topleft)
        bf.Time().timer(duration=600,callback=lambda :[bf.AudioManager().play_music("title_theme",-1,0) if bf.AudioManager().current_music != "title_theme" else 0]).start()
        self.timer1.start()
        self.timer2.start()

    def on_exit(self):
        self.timer1.stop()
        self.timer2.stop()

    def do_handle_event(self, event):
        if self._action_container.is_active("resume"):
            self.manager.transition_to_scene("editor",bf.FadeTransition)
        if self._action_container.is_active("l_click"):
            x,y = pygame.mouse.get_pos()

            x_index = (x - self.tileset_image.rect.left)// 8
            y_index = (y - self.tileset_image.rect.top) //8
            x = x // 8 
            y = y // 8
            if self.tileset.get_tile(x_index,y_index) == None:return
            self.picker.set_position(x*8,y*8)

        # if self._action_container.is_active("up") and self.picker.rect.y > self.tileset_image.rect.top:
        #     self.picker.set_position(*self.picker.rect.move(0,-8).topleft)
        # if self._action_container.is_active("down") and self.picker.rect.bottom < self.tileset_image.rect.bottom:
        #     self.picker.set_position(*self.picker.rect.move(0,8).topleft)
        # if self._action_container.is_active("left") and self.picker.rect.x > self.tileset_image.rect.left:
        #     self.picker.set_position(*self.picker.rect.move(-8,0).topleft)
        # if self._action_container.is_active("right") and self.picker.rect.right < self.tileset_image.rect.right:
        #     self.picker.set_position(*self.picker.rect.move(8,0).topleft)


    def do_update(self, dt):
        self.offset +=20 * dt
        self.offset = self.offset % self.bg1.rect.w
        self.bg1.set_position(self.offset,0)
        self.bg2.set_position(self.bg1.rect.left - self.bg2.rect.w,0)
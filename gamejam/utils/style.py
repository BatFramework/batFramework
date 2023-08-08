import batFramework as bf
import pygame
from math import sin

def draw_focused_func(self:bf.Button,camera:bf.Camera):
    self.draw(camera)
    p2 = self.rect.move(- (2*sin(pygame.time.get_ticks()*.01)),0).midleft
    p1 = (p2[0]-4,p2[1]-4)
    p0 = (p2[0]-4,p2[1]+4)
    pygame.draw.polygon(camera.surface,bf.color.SHADE_GB,bf.move_points((3,0),p0,p1,p2))
    pygame.draw.polygon(camera.surface,bf.color.LIGHT_GB,[p0,p1,p2])
    if self._activate_flash > 0:
        self.draw_effect(camera)


def draw(self:bf.Toggle,camera:bf.Camera):
    super(bf.Toggle,self).draw(camera)
    camera.surface.fill(self.activate_color if self.value else self.deactivate_color,(*self.rect.move(-4,-2).midright,4,4))

def stylize(e : bf.Entity):
    match e:

        case bf.TextBox():
            e.set_background_color(bf.color.DARK_GB).set_border_width(1).set_border_color(bf.color.SHADE_GB)
            stylize(e.label)
            e.label.set_background_color(bf.color.DARK_GB).set_padding((0,0)).set_outline(False)

        case bf.TitledFrame():
            e.set_border_color(bf.color.SHADE_GB).set_border_width(2).set_background_color(bf.color.DARK_GB)
            e.title_label.set_background_color(bf.color.BASE_GB).set_text_color(bf.color.LIGHT_GB)
            e.title_label.set_underline(True)

        case bf.Toggle():

            e.set_border_color(bf.color.DARK_GB).set_background_color(bf.color.BASE_GB).set_text_color(bf.color.LIGHT_GB).set_outline_color(bf.color.DARK_GB).set_feedback_color(bf.color.LIGHT_GB)
            
            e.set_italic(True)
            e.set_padding((4,4))


            e.activate_sfx = "click_fade"
            e.set_deactivate_color(bf.color.DARK_GB)
            e.set_activate_color(bf.color.LIGHT_GB)

            e.draw_focused = lambda cam,e=e : draw_focused_func(e,cam)
            e.draw = lambda camera,e=e : draw(e,camera)

        case bf.Container():
            e.set_border_width(2).set_border_color(bf.color.LIGHT_GB).set_background_color(bf.color.DARK_GB).set_padding((8,6))
            [stylize(child) for child in e.children]
            e.switch_focus_sfx = "click"
            e.add_entity = lambda entity : [bf.Container.add_entity(e,entity),stylize(entity),e]

        case bf.Button():
            e.set_border_color(bf.color.DARK_GB).set_background_color(bf.color.BASE_GB).set_text_color(bf.color.LIGHT_GB).set_outline_color(bf.color.DARK_GB).set_feedback_color(bf.color.LIGHT_GB)
            e.draw_focused = lambda cam,e=e : draw_focused_func(e,cam)
            e.set_italic(True)
            e.set_padding((4,4))
            e.activate_sfx = "click_fade"

        case bf.Label():
            e.set_border_color(bf.color.DARK_GB).set_background_color(bf.color.BASE_GB).set_text_color(bf.color.LIGHT_GB).set_outline_color(bf.color.DARK_GB)
            # e.set_italic(True)
        case _:
            pass
            # print("Can't stylize unknown entity :",e)


import batFramework as bf
import pygame
from math import sin

TOGGLE_INDICATOR_SIZE = [4, 4]
TOGGLE_INDICATOR_HALF_SIZE = [i // 2 for i in TOGGLE_INDICATOR_SIZE]
DEFAULT_PADDING = [2, 1]


class TextBoxIndicator(bf.Entity):
    def __init__(self) -> None:
        super().__init__((10,10),convert_alpha=True)
        self.set_visible(False)
        self.surface.fill((0,0,0,0))
        p2 = (0,0)
        p1 = (p2[0] + 4, p2[1] + 4)
        p0 = (p2[0], p2[1] + 8)

        self.double_surf = self.surface.copy()
        pygame.draw.polygon(self.surface, bf.color.LIGHT_GB, [p0, p1, p2])
        pygame.draw.polygon(self.surface, bf.color.LIGHT_GB, [p0, p1, p2])
        self.anchor = 0,0
        self.anim = bf.EasingAnimation(name="text_box_indicator",loop=True,update_callback=lambda x,self=self: self.set_position(self.anchor[0]+(0.2* sin(pygame.time.get_ticks() * 0.008)),self.anchor[1]))
        self.anim.start()
        
    def set_double(self,val:bool):
        self.double_surf = val

    def set_position(self, x, y):
        self.anchor = (x,y)
        return super().set_position(x, y)




def draw_focused_func(self: bf.Button, camera: bf.Camera):
    i = self.draw(camera)
    if i == 0:return 0
    p2 = self.rect.move(-(2 * sin(pygame.time.get_ticks() * 0.01)), 0).midleft
    p1 = (p2[0] - 4, p2[1] - 4)
    p0 = (p2[0] - 4, p2[1] + 4)
    pygame.draw.polygon(
        camera.surface, bf.color.SHADE_GB, bf.move_points((3, 0), p0, p1, p2)
    )
    pygame.draw.polygon(camera.surface, bf.color.LIGHT_GB, [p0, p1, p2])
    if self._activate_flash > 0:
        self.draw_effect(camera)
    return i+1

def _toggle_draw(self: bf.Toggle, camera: bf.camera):
    i = super(bf.Toggle, self).draw(camera)
    if i:
        camera.surface.fill(
            self.activate_color if self.value else self.deactivate_color,
            (
                *self.rect.move(
                    -TOGGLE_INDICATOR_SIZE[0] * 2, -TOGGLE_INDICATOR_HALF_SIZE[1]
                ).midright,
                *TOGGLE_INDICATOR_SIZE,
            ),
        )
        i+=1
    return i


def _toggle_align_text(self: bf.Toggle):
    tmp_rect = pygame.FRect(0, 0, *self.rect.size)

    match self._alignment:
        case bf.Alignment.LEFT:
            self._text_rect.centery = tmp_rect.centery
            self._text_rect.left = self._padding[0] + (
                self._border_radius[1]
                if len(self._border_radius) == 4
                else self._border_radius[0]
            )
        case bf.Alignment.RIGHT:
            self._text_rect.centery = tmp_rect.centery
            self._text_rect.right = (
                tmp_rect.w
                - TOGGLE_INDICATOR_SIZE[0]
                - self._padding[0]
                - (
                    self._border_radius[2]
                    if len(self._border_radius) == 4
                    else self._border_radius[0]
                )
            )
        case bf.Alignment.CENTER:
            self._text_rect.center = tmp_rect.move(-TOGGLE_INDICATOR_SIZE[0], 0).center
        case _:
            self._text_rect.center = tmp_rect.move(-TOGGLE_INDICATOR_SIZE[0], 0).center


def _toggle_compute_size(self: bf.Toggle):
    # print("TOGGLE COMPUTE SIZE")
    new_rect_size = list(self._text_rect.size)
    new_rect_size[0] += (
        self._padding[0] * 2 + TOGGLE_INDICATOR_SIZE[0] * 3
    )  # + self._border_radius[0] // 2 # +(2 if self._outline else 0)
    new_rect_size[1] += self._padding[1] * 2  # + (1 if self._outline else 0)
    if not self._manual_resized:
        if self._parent_resize_request:
            self.rect.w = (
                self._parent_resize_request[0]
                if self._parent_resize_request[0]
                else new_rect_size[0]
            )
            self.rect.h = (
                self._parent_resize_request[1]
                if self._parent_resize_request[1]
                else new_rect_size[1]
            )
        else:
            self.rect.size = new_rect_size


def stylize(entity: bf.Entity):
    match entity:
        case bf.TextBox():
            entity.set_background_color(bf.color.DARK_GB).set_border_width(
                1
            ).set_border_color(bf.color.SHADE_GB).set_padding(DEFAULT_PADDING)
            stylize(entity.label)
            entity.label.set_background_color(None).set_outline(False)
            entity.set_indicator(TextBoxIndicator())

        case bf.TitledFrame():
            entity.set_border_color(bf.color.SHADE_GB).set_border_width(
                2
            ).set_background_color(bf.color.DARK_GB)
            entity.title_label.set_background_color(bf.color.BASE_GB).set_text_color(
                bf.color.LIGHT_GB
            )
            entity.title_label.set_underline(True)

        case bf.Toggle():
            entity._parent_resize_request = None
            entity._compute_size = lambda self=entity: _toggle_compute_size(self)
            entity.align_text_rect = lambda self=entity: _toggle_align_text(self)
            entity.set_border_color(bf.color.DARK_GB).set_background_color(
                bf.color.BASE_GB
            ).set_text_color(bf.color.LIGHT_GB).set_outline_color(
                bf.color.DARK_GB
            ).set_feedback_color(
                bf.color.LIGHT_GB
            )
            entity.set_padding(DEFAULT_PADDING)

            entity.activate_sfx = "click_fade"
            entity.set_deactivate_color(bf.color.DARK_GB)
            entity.set_activate_color(bf.color.LIGHT_GB)

            entity.update_surface()
            entity.draw_focused = lambda cam, entity=entity: draw_focused_func(entity, cam)
            entity.draw = lambda camera, entity=entity: _toggle_draw(entity, camera)



        case bf.Container():
            [stylize(child) for child in entity.children]
            entity.set_border_width(2).set_border_color(
                bf.color.LIGHT_GB
            ).set_background_color(bf.color.DARK_GB).set_padding((6, 6)).set_gap(2)
            entity.update_content()
            entity.switch_focus_sfx = "click"
            entity.add_entity = lambda other_entity: [
                stylize(other_entity),
                bf.Container.add_entity(entity, other_entity),
                entity,
            ]
            if isinstance(entity,bf.TitledContainer):
                stylize(entity.title_label)
                entity.set_title_padding((6,2))
            if isinstance(entity,bf.ScrollingContainer):
                entity.set_scrollbar_color(bf.color.LIGHT_GB)
                entity.set_scrollbar_margin(3)
                entity.set_scrollbar_width(2)

        case bf.Button():
            entity.set_border_color(bf.color.DARK_GB).set_background_color(
                bf.color.BASE_GB
            ).set_text_color(bf.color.LIGHT_GB).set_outline_color(
                bf.color.DARK_GB
            ).set_feedback_color(
                bf.color.LIGHT_GB
            )
            entity.draw_focused = lambda cam, entity=entity: draw_focused_func(entity, cam)
            entity.set_padding(DEFAULT_PADDING)

            entity.activate_sfx = "click_fade"

        case bf.Label():
            entity.set_border_color(bf.color.DARK_GB).set_background_color(
                bf.color.SHADE_GB
            ).set_text_color(bf.color.LIGHT_GB).set_outline_color(bf.color.DARK_GB)
            entity.set_padding(DEFAULT_PADDING)

        case _:
            pass
            # print("Can't stylize unknown other_entity :",entity)

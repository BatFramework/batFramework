import batFramework as bf
import pygame
from .label import Label
from .interactiveEntity import InteractiveEntity


class Button(Label, InteractiveEntity):
    def __init__(self, text="", text_size=None, callback=None) -> None:
        self._image: pygame.Surface = None
        self._hover_surf = None
        bf.Label.__init__(self, text_size=text_size)
        bf.InteractiveEntity.__init__(self)
        # self._initialised = False
        self.set_background_color("gray19")
        self.set_text(text, text_size)
        self.activate_container = bf.ActionContainer(
            bf.Action("mouse").add_mouse_control(1),
            bf.Action("key").add_key_control(pygame.K_RETURN, pygame.K_SPACE),
        )
        self._callback = callback
        self._activate_flash = 0
        self._flash_animation_length = 15
        self._flash_duration = 8
        self._hovering = False
        self.feedback_color = bf.color.CLOUD_WHITE
        self.activate_sfx = None

    def set_feedback_color(self, color):
        self.feedback_color = color
        return self

    def get_bounding_box(self):
        yield from super().get_bounding_box()

    def set_image(self, surface: pygame.Surface):
        self._image = surface
        self.update_surface()

    def set_callback(self, callback):
        self._callback = callback

    def activate(self, bypass_focus=False):
        if (not self._focused) and (not bypass_focus) or self._activate_flash > 0:
            return
        if bypass_focus and not self._focused:
            self.get_focus()

        self._activate_flash = self._flash_animation_length
        if self.activate_sfx:
            bf.AudioManager().play_sound(self.activate_sfx)

        if self.parent_container:
            self.parent_container.lock_focus = True

    def process_event(self, event):
        self.activate_container.process_event(event)

    def update_surface(self):
        if not self._image:
            super().update_surface()
            # self.rect = self._image.get_rect(topleft= self.rect.topleft).inflate(*self._padding)
            # self.surface.fill((0,0,0,0))
            # self.surface.blit(self._image,(self._padding[0]//2,self._padding[1]//2))
        if (
            not self._hover_surf
            or self._hover_surf.get_size() != self.surface.get_size()
        ):
            self._hover_surf = self.surface.copy().convert_alpha()
            tmp = pygame.Surface(self.rect.size)
            tmp.fill((30, 30, 30))
            self._hover_surf.blit(tmp, (0, 0), special_flags=pygame.BLEND_ADD)

    def update(self, dt: float):
        if self.visible:
            if self.activate_container.is_active("key"):
                self.activate()
            elif self.rect.collidepoint(pygame.mouse.get_pos()): 
                if self.activate_container.is_active("mouse"):
                    self.activate(bypass_focus=True)
                else:
                    self._hovering = True
            else:
                self._hovering = False
        if self._activate_flash > 0:
            self._activate_flash -= 60 * dt
            if self._activate_flash < 0:
                if self._callback:
                    self._callback()
                if self.parent_container:
                    self.parent_container.lock_focus = False
        self.activate_container.reset()

    def draw_effect(self, camera):
        width = max(0, min(8, self.rect.h // 2 - 1, self.rect.w // 2 - 1)) * (
            self._activate_flash / self._flash_animation_length
        )
        # print(width)
        if int(width) > 0:
            pygame.draw.rect(
                camera.surface,
                self.feedback_color,
                camera.transpose(self.rect.inflate(2, 2)),
                int(width),
                *self._border_radius
            )

    def draw(self, camera):
        if not self.visible or not camera.intersects(self.rect):
            return False
        if self._hovering:
            camera.surface.blit(
                self._hover_surf,
                camera.transpose(self.rect),
                None,
                pygame.BLEND_ALPHA_SDL2,
            )
        else:
            super().draw(camera)
        if self._activate_flash > 0 and self._focused:
            self.draw_effect(camera)
        return True

    def draw_focused(self, camera):
        i = self.draw(camera)
        if i == 0 : return 0
        focus_width = 2
        pygame.draw.rect(
            camera.surface,
            bf.color.RIVER_BLUE,
            camera.transpose(self.rect.inflate(focus_width * 2, focus_width * 2)),
            focus_width,
            *self._border_radius
        )
        if self._activate_flash > 0:
            self.draw_effect(camera)
        return i+1

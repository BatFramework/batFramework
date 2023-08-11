import batFramework as bf
import pygame
from .button import Button


class Toggle(Button):
    def __init__(self,text,callback=None,default_value=False):
        self.value = default_value
        self.deactivate_color = bf.color.DARK_RED
        self.activate_color = bf.color.GREEN
        super().__init__(text)
        self.set_callback(callback)


    def set_deactivate_color(self,color):
        self.deactivate_color = color
        self.update_surface()

    def set_activate_color(self,color):
        self.activate_color = color
        self.update_surface()

    def update(self, dt: float):
        if self.activate_container.is_active("key"):
            self.activate()
        elif self.rect.collidepoint(pygame.mouse.get_pos()):
            if self.activate_container.is_active("mouse"):
                self.activate(bypass_focus=True)
            else:
                self._hovering = True
        else:
            self._hovering = False
        self.activate_container.reset()
        if self._activate_flash > 0 : 
            self._activate_flash -=60 * dt
            if self._activate_flash < 0: 
                if self._callback : 
                    self.toggle()
                    self._callback(self.value)
                if self.parent_container: self.parent_container.lock_focus = False

    def toggle(self,value=None):
        if value!=None:
            self.value =value
            if self._callback : self._callback(self.value)
        else:
            self.value = not self.value
        self.update_surface()

    # def update_aligment(self):
    #     tmp_rect = pygame.FRect(0,0,*self.rect.size)

    #     match self._alignement:
    #         case bf.Alignment.LEFT:
    #             self._text_rect.centery = tmp_rect.centery
    #             self._text_rect.left = self._padding[0] + (self._border_radius[1] if len(self._border_radius) == 4 else self._border_radius[0])
    #         case bf.Alignment.RIGHT:
    #             self._text_rect.centery = tmp_rect.centery
    #             self._text_rect.right = tmp_rect.w - self._padding[0] - (self._border_radius[2] if len(self._border_radius) == 4 else self._border_radius[0])
    #         case bf.Alignment.CENTER: 
    #             self._text_rect.center = tmp_rect.center
    #         case _:
    #             self._text_rect.center = tmp_rect.center


    # def _compute_size(self):
    #     new_rect_size = list(self._text_rect.inflate(self._padding).inflate(self._border_radius[0] // 2, 0).size)

    #     if not self._manual_resized:

    #         if self._parent_resize_request:

    #             self.rect.w = self._parent_resize_request[0] if self._parent_resize_request[0] else new_rect_size[0]
    #             self.rect.h = self._parent_resize_request[1] if self._parent_resize_request[1] else new_rect_size[1]
    #         else:
    #             self.rect.size = new_rect_size
    #             if self.parent_container: 
    #                 self.parent_container.update_content()
    #                 return True
    #     return False

    # def update_surface(self):

    #     font = self.get_font_set()

    #     if self._wraplength == None:
    #         wraplength = int(self._parent_resize_request[0]) if self._parent_resize_request and self._parent_resize_request[0] else 0
    #     else:
    #         wraplength = self._wraplength

    #     text_surface = font.render(
    #         self._text, bf.const.FONT_ANTIALIASING, self._text_color, None,wraplength)

    #     self._text_rect = text_surface.get_rect()


    #     if self._compute_size():return

    #     if self.rect.size != self.surface.get_size() : self.surface = pygame.Surface(self.rect.size).convert_alpha()
        
    #     self.align_text_rect()
    #     super().update_surface()

    #     if self._outline : self.draw_outline(font,wraplength)
    #     self.reset_font(font)

    #     self.surface.blit(text_surface, self._text_rect)
    #     # self._text_rect.move_ip(*self.rect.topleft)

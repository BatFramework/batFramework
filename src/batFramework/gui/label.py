import batFramework as bf
import pygame
from .frame import Frame


class Label(Frame):
    def __init__(self, text="", text_size=None, font_name=None):
        super().__init__()
        self._font_name = font_name
        self._font_object : pygame.Font = None
        self._text = ""
        self._text_size = bf.const.DEFAULT_TEXT_SIZE if not text_size else text_size
        self._padding = (0, 0)
        self._alignment = bf.Alignment.CENTER
        self._font_align = pygame.FONT_LEFT
        self._underline = False
        self._italic = False
        self._text_color = "white"
        self._initialised = False
        self._outline = False
        self._outline_color = "gray2"
        self._text_rect = pygame.Rect(0, 0, 0, 0)
        self._wraplength = None
        self.set_font(None)
        self.set_text(text, self._text_size)

    def set_wraplength(self, val: int):
        self._wraplength = val
        self.update_surface()

    def get_bounding_box(self):
        yield self.rect
        yield self._text_rect.move(*self.rect.topleft)

    def set_alignment(self, aligment: bf.Alignment):
        self._alignment = aligment
        self.update_surface()
        return self

    def set_outline(self, value: bool):
        self._outline = value
        self.update_surface()
        return self

    def set_outline_color(self, color):
        self._outline_color = color
        self.update_surface()
        return self

    def set_text_color(self, color):
        self._text_color = color
        self.update_surface()
        return self

    def set_text_alignment(self, align: int):
        if align == self._font_align:
            return self
        self._font_align = align
        self.update_surface()
        return self

    def set_italic(self, val: bool):
        if val == self._italic:
            return self
        self._italic = val
        self.update_surface()
        return self

    def set_underline(self, val: bool):
        if val == self._underline:
            return self
        self._underline = val
        self.update_surface()
        return self

    def set_padding(self, value):
        self._padding = value
        self.update_surface()
        if self.parent_container:
            self.parent_container.update_content()

        return self

    def set_font(self,filename):
        f : pygame.Font = bf.utils.get_font(filename,self._text_size)
        if f is None: return self
        self._font_object = f
        return self

    def set_text(
        self,
        text,
        size=None,
        align: int = pygame.FONT_LEFT,
        underline: bool = None,
        italic: bool = None,
    ):
        if size is not None:
            self._text_size = size
        if underline is not None:
            self._underline = underline
        if italic is not None:
            self._italic = italic
        self._font_align = align
        if text == self._text and self._initialised:
            return
        self._text = text
        self._initialised = True
        self._parent_resize_request = None
        self.update_surface()
        if self.parent_container:
            self.parent_container.update_content()
        return self

    def align_text_rect(self):
        tmp_rect = pygame.FRect(0, 0, *self.rect.size)
        if self._alignment in (bf.Alignment.LEFT, bf.Alignment.RIGHT):
            self._text_rect.centery = tmp_rect.centery
            x_offset = self._padding[0] + (self._border_radius[1] if len(self._border_radius) == 4 else self._border_radius[0])
            if self._alignment == bf.Alignment.RIGHT:
                x_offset = tmp_rect.w - x_offset
            self._text_rect.x = x_offset
        else:
            self._text_rect.center = tmp_rect.center

    def draw_outline(self, font: pygame.Font, wraplength):
        if self._outline:
            offset = int(self._text_size / 8) 
            # outline_surf = font.render(self._text, bf.const.FONT_ANTIALIASING, self._outline_color, None,wraplength)
            outline_surf = font.render(
                self._text, True, self._outline_color, None, wraplength
            )
            self.surface.blit(outline_surf, self._text_rect.move(offset, offset))
            self.surface.blit(outline_surf, self._text_rect.move(offset, 0))

    def init_font(self):
        self._font_object.align = self._font_align
        self._font_object.italic = self._italic
        self._font_object.underline = self._underline

    def reset_font(self):

        self._font_object.align = pygame.FONT_LEFT
        self._font_object.italic = False
        self._font_object.underline = False

    def _compute_size(self):
        new_rect_size = list(self._text_rect.size)
        new_rect_size[0] += (
            self._padding[0] * 2
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

    def update_surface(self):
        self.init_font()

        if self._wraplength is None:
            wraplength = int(self._parent_resize_request[0]) \
                if self._parent_resize_request and self._parent_resize_request[0] \
                else 0
        else:
            wraplength = self._wraplength

        text_surface  = self._font_object.render(
            self._text, bf.const.FONT_ANTIALIASING, self._text_color, None, wraplength
        )

        self._text_rect = text_surface.get_rect()

        self._compute_size()

        self.align_text_rect()
        super().update_surface()

        if self._outline:
            self.draw_outline(self._font_object, wraplength)

        self.reset_font()

        self.surface.blit(text_surface, self._text_rect)

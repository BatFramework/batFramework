import batFramework as bf
import pygame
from .shape import Shape
from typing import Self


class Label(Shape):
    _text_cache = {}

    def __init__(self, text: str) -> None:
        self.text = ""

        self.resized_flag: bool = False

        # Enable/Disable antialiasing
        self.antialias: bool = bf.FontManager().DEFAULT_ANTIALIAS

        self.text_size = bf.FontManager().DEFAULT_TEXT_SIZE

        self.auto_wraplength: bool = False

        self.alignment: bf.alignment = bf.alignment.CENTER

        self.text_color: tuple[int, int, int] | str = "black"

        self.text_outline_color: tuple[int, int, int] | str = "gray50"

        self.text_outline_surface: pygame.Surface = None

        self._text_outline_mask = pygame.Mask((3, 3), fill=True)

        # font name (given when loaded by utils) to use for the text
        self.font_name = None
        # reference to the font object
        self.font_object = None
        # Rect containing the text of the label
        self.text_rect = pygame.FRect(0,0,0,0)
        # text surface (result of font.render)
        self.text_surface: pygame.Surface = pygame.Surface((0, 0))
        self.do_caching: bool = False

        self.show_text_outline: bool = False

        self.is_italic: bool = False

        self.is_bold: bool = False

        self.is_underlined: bool = False

        super().__init__((0, 0))
        self.set_padding((10, 4))
        self.set_debug_color("blue")
        self.set_color("gray50")
        self.set_autoresize(True)
        self.set_font(force=True)
        self.set_text(text)

    @staticmethod
    def clear_cache():
        Label._text_cache = {}

    def enable_caching(self) -> Self:
        self.do_caching = True
        return self

    def disable_caching(self) -> Self:
        self.do_caching = False
        return self

    def set_text_color(self, color) -> Self:
        self.text_color = color
        self.dirty_surface = True
        return self

    def set_italic(self, value: bool) -> Self:
        if value == self.is_italic:
            return self
        self.is_italic = value
        if self.autoresize_h or self.autoresize_w: 
            self.dirty_shape = True
        else:
            self.dirty_surface = True
        return self

    def set_bold(self, value: bool) -> Self:
        if value == self.is_bold:
            return self
        self.is_bold = value
        if self.autoresize_h or self.autoresize_w: 
            self.dirty_shape = True
        else:
            self.dirty_surface = True
        return self

    def set_underlined(self, value: bool) -> Self:
        if value == self.is_underlined:
            return self
        self.is_underlined = value
        self.dirty_surface = True
        return self

    def set_text_outline_matrix(self, matrix: list[list[0 | 1]]) -> Self:
        if matrix is None:
            matrix = [[0 for _ in range(3)] for _ in range(3)]
        for y in range(3):
            for x in range(3):
                self._text_outline_mask.set_at((x, y), matrix[2 - y][2 - x])
        self.dirty_surface = True
        return self

    def set_text_outline_color(self, color) -> Self:
        self.text_outline_color = color
        self.dirty_surface = True
        return self

    def enable_text_outline(self) -> Self:
        self.show_text_outline = True
        self.dirty_surface = True
        return self

    def disable_text_outline(self) -> Self:
        self.show_text_outline = False
        self.dirty_surface = True
        return self

    def __str__(self) -> str:
        return f"Label({self.text})"

    def set_alignment(self, alignment: bf.alignment) -> "Label":
        self.alignment = alignment
        self.dirty_surface = True
        return self

    def set_auto_wraplength(self, val: bool) -> "Label":
        self.auto_wraplength = val
        if self.autoresize_h or self.autoresize_w: 
            self.dirty_shape = True
        else:
            self.dirty_surface = True
        return self

    def get_debug_outlines(self):
        yield from super().get_debug_outlines()
        yield (self.text_rect.move(*self.rect.topleft),"purple")
        
    def set_font(self, font_name: str = None, force: bool = False) -> Self:
        if font_name == self.font_name and not force:
            return self
        self.font_name = font_name
        self.font_object = bf.FontManager().get_font(self.font_name, self.text_size)
        if self.autoresize_h or self.autoresize_w: 
            self.dirty_shape = True
        else:
            self.dirty_surface = True
        return self

    def set_text_size(self, text_size: int) -> Self:
        text_size = round(text_size / 2) * 2
        if text_size == self.text_size:
            return self
        self.text_size = text_size
        self.font_object = bf.FontManager().get_font(self.font_name, self.text_size)
        if self.autoresize_h or self.autoresize_w: 
            self.dirty_shape = True
        return self

    def get_text_size(self) -> int:
        return self.text_size

    def is_antialias(self) -> bool:
        return self.antialias

    def set_antialias(self, value: bool) -> Self:
        self.antialias = value
        self.dirty_surface = True
        return self

    def set_text(self, text: str) -> Self:
        if text == self.text:
            return self
        self.text = text
        self.dirty_shape = True
        return self

    def get_min_required_size(self)->tuple[float,float]:
        if not (self.autoresize_w or  self.autoresize_h) : 
            return self.rect.size
        if not self.text_rect:
            params = {
                "font_name": self.font_object.name,
                "text": self.text,
                "antialias": False,
                "color": "white",
                "bgcolor": "black",  # if (self.has_alpha_color() or self.draw_mode == bf.drawMode.TEXTURED) else self.color,
                "wraplength": int(self.get_padded_width()) if self.auto_wraplength else 0,
            }

            self.text_rect.size = self._render_font(params).get_size()
        res = self.inflate_rect_by_padding((0,0,*self.text_rect.size)).size
        # return res
        return res[0] if self.autoresize_w else self.rect.w, res[1] if self.autoresize_h else self.rect.h

    def get_text(self) -> str:
        return self.text

    def _render_font(self, params: dict) -> pygame.Surface:
        key = tuple(params.values())

        cached_value = Label._text_cache.get(key, None)

        if self.draw_mode == bf.drawMode.SOLID:
            if cached_value is None:
                params.pop("font_name")

                #save old settings                
                old_italic = self.font_object.get_italic()
                old_bold = self.font_object.get_bold()
                old_underline = self.font_object.get_underline()

                #setup font
                self.font_object.set_italic(self.is_italic)
                self.font_object.set_bold(self.is_bold)
                self.font_object.set_underline(self.is_underlined)
                
                surf = self.font_object.render(**params)

                # reset font 
                self.font_object.set_italic(old_italic)
                self.font_object.set_bold(old_bold)
                self.font_object.set_underline(old_underline)

                if self.do_caching:
                    Label._text_cache[key] = surf
            else:
                surf = cached_value
        else:
            params.pop("font_name")
            surf = self.font_object.render(**params)

        return surf

    def _build_layout(self) -> None:

        params = {
            "font_name": self.font_object.name,
            "text": self.text,
            "antialias": False,
            "color": "white",
            "bgcolor": "black",  # if (self.has_alpha_color() or self.draw_mode == bf.drawMode.TEXTURED) else self.color,
            "wraplength": int(self.get_padded_width()) if self.auto_wraplength else 0,
        }

        self.text_rect.size = self._render_font(params).get_size()
        if self.autoresize_h or self.autoresize_w: 
            target_rect = self.inflate_rect_by_padding((0,0,*self.text_rect.size))
            if not self.autoresize_w : target_rect.w = self.rect.w
            if not self.autoresize_h : target_rect.h = self.rect.h
            if self.rect.size != target_rect.size:
                self.set_size(target_rect.size)
                self.build()
                return
        padded = self.get_padded_rect().move(-self.rect.x,-self.rect.y)
        self.align_text(self.text_rect,padded,self.alignment)

    def _paint_text(self) -> None:
        if self.font_object is None:
            print(f"No font for widget with text : '{self}' :(")
            return

        params = {
            "font_name": self.font_object.name,
            "text": self.text,
            "antialias": self.antialias,
            "color": self.text_color,
            "bgcolor": None,  # if (self.has_alpha_color() or self.draw_mode == bf.drawMode.TEXTURED) else self.color,
            "wraplength": int(self.get_padded_width()) if self.auto_wraplength else 0,
        }
        self.text_surface = self._render_font(params)

        if self.show_text_outline:
            self.text_outline_surface = (
                pygame.mask.from_surface(self.text_surface)
                .convolve(self._text_outline_mask)
                .to_surface(setcolor=self.text_outline_color, unsetcolor=(0, 0, 0, 0))
            )


        l = []
        if self.show_text_outline:
            l.append(
                (
                    self.text_outline_surface,
                    self.text_rect.move(-1, self.relief - self.get_relief() - 1),
                )
            )
        l.append(
            (self.text_surface, self.text_rect.move(0, self.relief - self.get_relief()))
        )
        self.surface.fblits(l)

    def align_text(self,text_rect:pygame.FRect,area:pygame.FRect,alignment: bf.alignment):
        if alignment == bf.alignment.LEFT : alignment = bf.alignment.MIDLEFT
        elif alignment == bf.alignment.MIDRIGHT : alignment = bf.alignment.MIDRIGHT

        pos = area.__getattribute__(alignment.value)
        text_rect.__setattr__(alignment.value,pos)

    def build(self) -> None:
        super().build()
        self._build_layout()

    def paint(self)->None:
        super().paint()
        if self.font_object:
            self._paint_text()

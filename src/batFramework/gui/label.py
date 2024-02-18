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
        # font name (given when loaded by utils) to use for the text
        self.font_name = None
        # reference to the font object
        self.font_object = None
        # Rect containing the text of the label
        self.text_rect = None
        # text surface (result of font.render)
        self.text_surface: pygame.Surface | None = None

        self.do_caching : bool = False
        super().__init__(width=0, height=0)
        self.set_padding((10, 4))
        self.set_debug_color("blue")
        self.set_color("white")
        self.set_autoresize(True)
        self.set_font(force=True)
        self.set_text(text)


    @staticmethod
    def clear_cache():
        Label._text_cache = {}
    
    def enable_caching(self)->Self:
        self.do_caching = True
        return self

    def disable_caching(self)->Self:
        self.do_caching = False
        return self

    def set_text_color(self, color) -> Self:
        self.text_color = color
        self.build()
        return self

    def to_string_id(self) -> str:
        return f"Label({self.text})"

    def set_alignment(self, alignment: bf.alignment) -> "Label":
        self.alignment = alignment
        self.build()
        return self

    def set_auto_wraplength(self, val: bool) -> "Label":
        self.auto_wraplength = val
        self.build()
        return self

    def get_bounding_box(self):
        yield from super().get_bounding_box()
        if self.text_rect:
            yield self.text_rect.move(*self.rect.topleft)

    def set_font(self, font_name: str = None, force: bool = False) -> "Label":
        if font_name == self.font_name and not force:
            return self
        self.font_name = font_name
        self.font_object = bf.FontManager().get_font(self.font_name, self.text_size)
        self.build()
        return self

    def set_text_size(self, text_size: int) -> "Label":
        text_size = round(text_size / 2) * 2
        if text_size == self.text_size:
            return self
        self.text_size = text_size
        self.font_object = bf.FontManager().get_font(self.font_name, self.text_size)
        self.build()
        return self

    def get_text_size(self) -> int:
        return self.text_size

    def is_antialias(self) -> bool:
        return self.antialias

    def set_antialias(self, value: bool) -> "Label":
        self.antialias = value
        self.build()
        return self

    def set_text(self, text: str) -> "Label":
        if text == self.text:
            return self
        self.text = text
        self.build()
        return self

    def get_text(self) -> str:
        return self.text


    def get_min_required_size(self)->tuple[float,float]:
        return (0,0) if not self.font_object else self.inflate_rect_by_padding(pygame.FRect(0,0,*self.font_object.size(self.text))).size

    def _build_text(self) -> None:
        if self.font_object is None:
            print(f"No font for '{self.to_string_id()}' :(")
            return
        # render(text, antialias, color, bgcolor=None, wraplength=0) -> Surface
        params = {
            "font_name":self.font_object.name,
            "text":self.text,
            "antialias":self.antialias,
            "color":self.text_color,
            "bgcolor":None if (self.has_alpha_color() or self.draw_mode == bf.drawMode.TEXTURED) else self.color,
            "wraplength":int(self.get_content_width()) if self.auto_wraplength else 0
            }
        
        key = tuple(params.values())
        cached_value =  Label._text_cache.get(key,None)
        if self.draw_mode == bf.drawMode.SOLID:
            if cached_value is None:
                if self.do_caching : 
                    Label._text_cache[key] = self.text_surface
                params.pop("font_name")
                self.text_surface = self.font_object.render(**params)
            else:
                self.text_surface = cached_value

        self.text_rect = self.text_surface.get_frect(topleft = self.get_content_rect_rel().topleft)




    def _build_layout(self) -> None:
        if self.text_rect is None : return
        if self.autoresize:
            target_rect = self.inflate_rect_by_padding(self.text_rect)
            if self.rect.size != target_rect.size:
                self.resized_flag = True
                self.set_size(* target_rect.size)
                return
        if self.alignment == bf.alignment.CENTER:
            self.text_rect.center = self.get_content_rect_rel().center
        elif self.alignment == bf.alignment.LEFT:
            self.text_rect.topleft = self.get_content_rect_rel().topleft
        elif self.alignment == bf.alignment.RIGHT:
            self.text_rect.topright = self.get_content_rect_rel().topright
        if self.resized_flag:
            self.resized_flag = False
            if self.parent:
                # print("Children modified call")
                self.parent.children_modified()

        self.surface.fblits([(self.text_surface, self.text_rect)])

    def build(self) -> None:
        super().build()
        if not self.font_object:
            return
        self._build_text()
        self._build_layout()
        self.apply_constraints()

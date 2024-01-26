import batFramework as bf
import pygame
from .shape import Shape
from typing import Self

class Label(Shape):
    _text_cache = {}
    def __init__(self, text: str) -> None:
        self._text = ""

        self._resized_flag: bool = False

        # Enable/Disable antialiasing
        self._antialias: bool = True

        self._text_size = bf.FontManager().DEFAULT_TEXT_SIZE

        self.auto_wraplength: bool = False

        self._alignment: bf.Alignment = bf.Alignment.CENTER

        self._text_color: tuple[int, int, int] | str = "black"
        # font name (given when loaded by utils) to use for the text
        self._font_name = None
        # reference to the font object
        self._font_object = None
        # Rect containing the text of the label
        self._text_rect = None
        # text surface (result of font.render)
        self._text_surface: pygame.Surface | None = None

        self._do_caching : bool = False
        super().__init__(width=0, height=0)
        self.set_padding((10, 4))
        self.set_debug_color("blue")
        self.set_color(bf.color.CLOUD_WHITE)
        self.set_autoresize(True)
        self.set_font(force=True)
        self.set_text(text)


    @staticmethod
    def clear_cache():
        Label._text_cache = {}
    
    def enable_caching(self)->Self:
        self._do_caching = True
        return self

    def disable_caching(self)->Self:
        self._do_caching = False
        return self

    def set_text_color(self, color) -> Self:
        self._text_color = color
        self.build()
        return self

    def to_string_id(self) -> str:
        return f"Label({self._text})"

    def set_alignment(self, alignment: bf.Alignment) -> "Label":
        self._alignment = alignment
        self.build()
        return self

    def set_auto_wraplength(self, val: bool) -> "Label":
        self.auto_wraplength = val
        self.build()
        return self

    def get_bounding_box(self):
        yield from super().get_bounding_box()
        if self._text_rect:
            yield self._text_rect.move(*self.rect.topleft)

    def set_font(self, font_name: str = None, force: bool = False) -> "Label":
        if font_name == self._font_name and not force:
            return self
        self._font_name = font_name
        self._font_object = bf.FontManager().get_font(self._font_name, self._text_size)
        self.build()
        return self

    def set_text_size(self, text_size: int) -> "Label":
        text_size = round(text_size / 2) * 2
        if text_size == self._text_size:
            return self
        self._text_size = text_size
        self._font_object = bf.FontManager().get_font(self._font_name, self._text_size)
        self.build()
        return self

    def get_text_size(self) -> int:
        return self._text_size

    def is_antialias(self) -> bool:
        return self._antialias

    def set_antialias(self, value: bool) -> "Label":
        self._antialias = value
        self.build()
        return self

    def set_text(self, text: str) -> "Label":
        if text == self._text:
            return self
        self._text = text
        self.build()
        return self

    def get_text(self) -> str:
        return self._text


    def get_min_required_size(self)->tuple[float,float]:
        return (0,0) if not self._font_object else self.inflate_rect_by_padding(pygame.FRect(0,0,*self._font_object.size(self._text))).size

    def _build_text(self) -> None:
        if self._font_object is None:
            print(f"No font for '{self.to_string_id()}' :(")
            return
        # render(text, antialias, color, bgcolor=None, wraplength=0) -> Surface

        params = {
            "font_name":self._font_object.name,
            "text":self._text,
            "antialias":self._antialias,
            "color":self._text_color,
            "bgcolor":self._color,
            "wraplength":int(self.get_content_width()) if self.auto_wraplength else 0
            }
        
        key = tuple(params.values())
        cached_value =  Label._text_cache.get(key,None)
        if cached_value != None:
            self._text_surface = cached_value
        else:
            params.pop("font_name")
            self._text_surface = self._font_object.render(**params)
            if self._do_caching:
                Label._text_cache[key] = self._text_surface
        self._text_rect = self._text_surface.get_frect(topleft = self.get_content_rect_rel().topleft)

    def _build_layout(self) -> None:
        if self._text_rect is None : return
        if self.autoresize:
            target_rect = self.inflate_rect_by_padding(self._text_rect)
            if self.rect.size != target_rect.size:
                self._resized_flag = True
                self.set_size(* target_rect.size)
                return
        if self._alignment == bf.Alignment.CENTER:
            self._text_rect.center = self.get_content_rect_rel().center
        elif self._alignment == bf.Alignment.LEFT:
            self._text_rect.topleft = self.get_content_rect_rel().topleft
        elif self._alignment == bf.Alignment.RIGHT:
            self._text_rect.topright = self.get_content_rect_rel().topright
        if self._resized_flag:
            self._resized_flag = False
            if self.parent:
                # print("Children modified call")
                self.parent.children_modified()

        self.surface.fblits([(self._text_surface, self._text_rect)])

    def build(self) -> None:
        super().build()
        if not self._font_object:
            return
        self._build_text()
        self._build_layout()
        self.apply_constraints()

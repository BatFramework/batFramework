from math import ceil
import pygame
from .widget import Widget
import batFramework as bf
from typing import Literal, Self,Union

class TextWidget(Widget):
    def __init__(self, text:str):
        super().__init__()
        self.text = text

        # Allows scrolling the text
        self.allow_scroll : bool = True

        # Scroll variable
        # TODO make scroll work
        self.scroll :pygame.Vector2 = pygame.Vector2(0,0)

        # Enable/Disable antialiasing
        self.antialias: bool = bf.FontManager().DEFAULT_ANTIALIAS

        self.text_size = bf.FontManager().DEFAULT_FONT_SIZE

        self.auto_wraplength: bool = False

        self.text_color: tuple[int, int, int] | str = "black"

        self.text_bg_color : tuple[int,int,int]| str |  None = None


        self.text_outline_color: tuple[int, int, int] | str = "gray50"

        self._text_outline_mask = pygame.Mask((3, 3), fill=True)

        self.line_alignment = pygame.FONT_LEFT
        # font name (given when loaded by utils) to use for the text

        self.font_name = None
        # reference to the font object
        self.font_object = None
        # Rect containing the text of the label
        self.show_text_outline: bool = False

        self.is_italic: bool = False

        self.is_bold: bool = False

        self.is_underlined: bool = False

        super().__init__()
        self.set_debug_color("purple")
        self.set_autoresize(True)
        self.set_font(force=True)
        self.set_convert_alpha(True)


    def set_padding(self, value): # can't set padding
        return self

    def __str__(self) -> str:
        return f"TextWidget({repr(self.text)})"
    
    def set_allow_scroll(self, value:bool)->Self:
        if self.allow_scroll == value: return self
        self.allow_scroll = value
        self.dirty_surface = True
        return self

    def set_scroll(self,x=None,y=None)->Self:
        x = x if x is not None else self.scroll.x
        y = y if y is not None else self.scroll.y

        self.scroll.update(x,y)
        self.dirty_surface = True
        return self

    def scroll_by(self,x=0,y=0)->Self:
        self.scroll += x,y
        self.dirty_surface = True
        return self

    def set_text_color(self, color) -> Self:
        self.text_color = color
        self.dirty_surface = True
        return self

    def set_text_bg_color(self, color) -> Self:
        self.text_bg_color = color
        self.set_convert_alpha(color is None)
        self.dirty_surface = True
        return self


    def top_at(self, x, y):
        return None

    def set_line_alignment(self, alignment: Union[Literal["left"], Literal["right"], Literal["center"]]) -> Self:
        self.line_alignment = alignment
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
    
    def set_text_outline_mask_size(self,size:tuple[int,int])->Self:
        old_size = self._text_outline_mask.get_size()
        min_w, min_h = min(old_size[0], size[0]), min(old_size[1], size[1])
        m = [
            [self._text_outline_mask.get_at((x, y)) for x in range(min_w)]
            for y in range(min_h)
        ]
        self._text_outline_mask = pygame.Mask(size, fill=True)
        self.set_text_outline_matrix(m)
        return self

    def set_text_outline_matrix(self, matrix: list[list[0 | 1]]) -> Self:
        if matrix is None:
            matrix = [[0 for _ in range(3)] for _ in range(3)]
        for y in range(3):
            for x in range(3):
                self._text_outline_mask.set_at((x, y), matrix[2 - y][2 - x])
        self.dirty_shape = True
        return self

    def set_text_outline_color(self, color) -> Self:
        self.text_outline_color = color
        self.dirty_surface = True
        return self

    def set_show_text_outline(self,value:bool) -> Self:
        self.show_text_outline = value
        self.dirty_shape = True
        return self

    def set_auto_wraplength(self, val: bool) -> Self:
        self.auto_wraplength = val
        if self.autoresize_h or self.autoresize_w:
            self.dirty_shape = True
        else:
            self.dirty_surface = True
        return self

    def get_debug_outlines(self):
        if self.visible:
            yield from super().get_debug_outlines()

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
        text_size = (text_size // 2) * 2
        if text_size == self.text_size:
            return self
        self.text_size = text_size
        self.font_object = bf.FontManager().get_font(self.font_name, self.text_size)
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

    def get_min_required_size(self) -> tuple[float, float]:
        if not self.font_object : return 0,0

        tmp_text = self.text
        if self.text.endswith('\n'):
            tmp_text+=" " # hack to have correct size if ends with newline
        params = {
            "font_name": self.font_object.name,
            "text": tmp_text,
            "antialias": self.antialias,
            "color": self.text_color,
            "bgcolor": self.text_bg_color,
            "wraplength": int(self.get_inner_width()) if self.auto_wraplength and not self.autoresize_w else 0,
        }

        size = list(self._render_font(params).get_size())
        size[1]= max(size[1],self.font_object.get_ascent() - self.font_object.get_descent())
        if not self.show_text_outline:
            return size
        s = self._get_outline_offset()
        return size[0] + s[0]*2, size[1] + s[1]*2
    

    def get_text(self) -> str:
        return self.text

    def _render_font(self, params: dict) -> pygame.Surface:
        params.pop("font_name")
        # save old settings
        old_italic = self.font_object.get_italic()
        old_bold = self.font_object.get_bold()
        old_underline = self.font_object.get_underline()
        old_align = self.font_object.align
        # setup font
        self.font_object.set_italic(self.is_italic)
        self.font_object.set_bold(self.is_bold)
        self.font_object.set_underline(self.is_underlined)
        self.font_object.align = self.line_alignment
        surf = self.font_object.render(**params)
        # reset font
        self.font_object.set_italic(old_italic)
        self.font_object.set_bold(old_bold)
        self.font_object.set_underline(old_underline)
        self.font_object.align = old_align
        return surf

    def _get_outline_offset(self)->tuple[int,int]:
        mask_size = self._text_outline_mask.get_size()
        return  mask_size[0]//2,mask_size[1]//2


    def build(self) -> bool:
        """
        return True if size changed
        """
        target_size = self.resolve_size(self.get_min_required_size())
        if self.rect.size != target_size:
            self.set_size(target_size)
            return True
        return False
        


    def paint(self) -> None:
        self._resize_surface()
        if self.font_object is None:
            print(f"No font for widget with text : '{self}' :(")
            return
        
            
        wrap = int(self.get_inner_width()) if self.auto_wraplength and not self.autoresize_w else 0
        params = {
            "font_name": self.font_object.name,
            "text": self.text,
            "antialias": self.antialias,
            "color": self.text_color,
            "bgcolor": self.text_bg_color if not self.show_text_outline else None,
            "wraplength": wrap,
        }

        if self.text_bg_color is None : 
            self.surface = self.surface.convert_alpha()

        bg_fill_color = (0, 0, 0, 0) if self.text_bg_color is None else  self.text_bg_color 
        self.surface.fill(bg_fill_color)

        text_surf = self._render_font(params)

        if self.show_text_outline:
            mask = pygame.mask.from_surface(text_surf).convolve(self._text_outline_mask)
            outline_surf = mask.to_surface(
                setcolor=self.text_outline_color,
                unsetcolor=bg_fill_color
            )

            outline_surf.blit(text_surf,self._get_outline_offset())
            text_surf = outline_surf

        self.surface.blit(text_surf, -self.scroll)

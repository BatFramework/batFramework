import batFramework as bf
import pygame
from .shape import Shape
from .textWidget import TextWidget
from typing import Literal, Self,Union
from math import ceil

class Label(Shape):

    def __init__(self, text: str = "") -> None:
        super().__init__((0, 0))
        self.alignment: bf.alignment = bf.alignment.CENTER
        self.text_widget = TextWidget(text)
        self.set_padding((10, 4))
        self.set_debug_color("blue")
        self.set_color("gray50")
        self.set_autoresize(True)
        self.set_font(force=True)
        self.add(self.text_widget)
        
    def __str__(self) -> str:
        return f"Label({repr(self.text_widget.text)})"

    def set_visible(self, value):
        self.text_widget.set_visible(value)
        return super().set_visible(value)

    def set_allow_scroll(self, value:bool)->Self:
        self.text_widget.set_allow_scroll(value)
        return self

    def set_line_alignment(self, alignment: int) -> Self:
        """
        alignment: One of pygame.FONT_CENTER, pygame.FONT_LEFT, pygame.FONT_RIGHT
        """
        self.text_widget.set_line_alignment(alignment)
        return self
    
    def set_text_color(self, color) -> Self:
        self.text_widget.set_text_color(color)
        return self

    def set_italic(self, value: bool) -> Self:
        self.text_widget.set_italic(value)
        return self

    def set_bold(self, value: bool) -> Self:
        self.text_widget.set_bold(value)
        return self

    def set_underlined(self, value: bool) -> Self:
        self.text_widget.set_underlined(value)
        return self

    def set_text_outline_mask_size(self,size:tuple[int,int])->Self:
        self.text_widget.set_text_outline_mask_size(size)
        return self

    def set_text_outline_matrix(self, matrix: list[list[0 | 1]]) -> Self:
        self.text_widget.set_text_outline_matrix(matrix)
        return self

    def set_text_outline_color(self, color) -> Self:
        self.text_widget.set_text_outline_color(color)
        return self

    def set_text_bg_color(self, color) -> Self:
        self.text_widget.set_text_bg_color(color)
        return self

    def set_show_text_outline(self,value:bool) -> Self:
        self.text_widget.set_show_text_outline(value)
        return self

    def set_alignment(self, alignment: bf.alignment) -> Self:
        self.alignment = alignment
        self.dirty_shape = True
        return self

    def set_auto_wraplength(self, val: bool) -> Self:
        self.text_widget.set_auto_wraplength(val)
        return self

    def get_debug_outlines(self):
        if self.visible:
            yield from super().get_debug_outlines()
            yield from self.text_widget.get_debug_outlines()

    def set_font(self, font_name: str = None, force: bool = False) -> Self:
        self.text_widget.set_font(font_name,force)
        return self

    def set_text_size(self, text_size: int) -> Self:
        self.text_widget.set_text_size(text_size)
        return self

    def get_text_size(self) -> int:
        return self.text_widget.text_size

    def is_antialias(self) -> bool:
        return self.text_widget.antialias

    def set_antialias(self, value: bool) -> Self:
        self.text_widget.set_antialias(value)
        return self

    def set_text(self, text: str) -> Self:
        self.text_widget.set_text(text)
        return self

    def get_min_required_size(self) -> tuple[float, float]:
        return self.expand_rect_with_padding(
            (0, 0, *self.text_widget.get_min_required_size())
        ).size

    def get_text(self) -> str:
        return self.text_widget.text

    def align_text(
        self, text_rect: pygame.FRect, area: pygame.FRect, alignment: bf.alignment
    ):
        if alignment == bf.alignment.LEFT:
            alignment = bf.alignment.MIDLEFT
        elif alignment == bf.alignment.MIDRIGHT:
            alignment = bf.alignment.MIDRIGHT

        pos = area.__getattribute__(alignment.value)
        text_rect.__setattr__(alignment.value, pos)
        text_rect.y = ceil(text_rect.y)

    def build(self):
        ret = False
        target_size = self.resolve_size(self.get_min_required_size())
        if self.rect.size != target_size :
            self.set_size(target_size)
            self.text_widget.set_size(self.get_inner_rect().size)
            ret = True

        padded = self.get_inner_rect()
        self.align_text(self.text_widget.rect, padded, self.alignment)
        return ret
    
    def apply_pre_updates(self):
        if self.text_widget.dirty_shape:
            self.dirty_shape =True
        return super().apply_pre_updates()
    
import pygame
import re
from typing import List, Tuple, Self


import batFramework as bf
from .label import Label
from .textWidget import TextWidget

_COLOR_TAG = re.compile(
    r'\[color=(?P<color>[^\]]+)\](?P<text>.*?)\[/color\]',
    re.DOTALL
)

def parse_segments(text: str, default_color):
    """
    Returns list of (substring, color).
    """
    segments = []
    idx = 0

    for m in _COLOR_TAG.finditer(text):
        s, e = m.span()

        if s > idx:
            segments.append((text[idx:s], default_color))

        seg_color = m.group("color")
        seg_text = m.group("text")
        segments.append((seg_text, seg_color))

        idx = e

    if idx < len(text):
        segments.append((text[idx:], default_color))

    return segments
class RichTextWidget(TextWidget):

    def __init__(self, text: str):
        super().__init__(text)
        self.default_color = self.text_color  # fallback

    def set_text_color(self, color) -> Self:
        self.default_color = color
        return super().set_text_color(color)

    # -------- SIZE CALCULATION ---------------------------------------------

    def get_min_required_size(self) -> tuple[float, float]:
        if not self.font_object:
            return (0, 0)

        segments = parse_segments(self.text, self.default_color)

        line_width = 0
        max_width = 0
        total_height = 0
        line_height = 0

        for seg_text, seg_color in segments:
            parts = seg_text.split("\n")

            for i, part in enumerate(parts):
                text = part if part else " "

                params = {
                    "font_name": self.font_object.name,
                    "text": text,
                    "antialias": self.antialias,
                    "color": seg_color,
                    "bgcolor": None,
                    "wraplength": 0,
                }

                surf = self._render_font(params)
                w, h = surf.get_size()
                line_height = max(line_height, h)
                line_width += w

                if i < len(parts) - 1:
                    # newline ends current line
                    max_width = max(max_width, line_width)
                    total_height += line_height

                    # reset for next line
                    line_width = 0
                    line_height = 0

        # last line
        max_width = max(max_width, line_width)
        total_height += line_height

        if self.show_text_outline:
            off = self._get_outline_offset()
            max_width += off[0] * 2
            total_height += off[1] * 2

        return (max_width, total_height)

    # -------- PAINT ---------------------------------------------------------

    def paint(self) -> None:
        self._resize_surface()
        if self.font_object is None:
            return

        bg = (0,0,0,0) if self.text_bg_color is None else self.text_bg_color
        self.surface.fill(bg)
        segments = parse_segments(self.text, self.default_color)

        cursor_x = 0
        cursor_y = 0
        rendered = []
        max_line_height = 0

        for seg_text, seg_color in segments:

            parts = seg_text.split("\n")

            for i, part in enumerate(parts):

                text = part if part else " "
                params = {
                    "font_name": self.font_object.name,
                    "text": text,
                    "antialias": self.antialias,
                    "color": seg_color,
                    "bgcolor": None,
                    "wraplength": 0,
                }

                surf = self._render_font(params)
                w, h = surf.get_size()

                if i == 0:
                    # Continue current line
                    pass
                else:
                    # newline → move down one line
                    cursor_x = 0
                    cursor_y += max_line_height
                    max_line_height = 0

                # Outline
                if self.show_text_outline:
                    mask = pygame.mask.from_surface(surf).convolve(self._text_outline_mask)
                    outline_surf = mask.to_surface(
                        setcolor=self.text_outline_color,
                        unsetcolor=bg
                    )
                    outline_surf.blit(surf, self._get_outline_offset())
                    surf = outline_surf

                rendered.append((surf, cursor_x, cursor_y))
                cursor_x += w
                max_line_height = max(max_line_height, h)

        # Draw everything
        for surf, x, y in rendered:
            self.surface.blit(surf, (x - self.scroll.x, y - self.scroll.y))



class RichLabel(Label):

    def __init__(self, text: str = ""):
        super().__init__("") 
        self.text_widget = RichTextWidget(text)
        self.add(self.text_widget)

    def set_text(self, text: str):
        self.text_widget.set_text(text)
        self.dirty_shape = True
        return self

    def set_text_color(self, color):
        self.text_widget.set_text_color(color)
        self.dirty_shape = True
        return self

    def set_text_bg_color(self, color):
        super().set_text_bg_color(color)
        self.text_widget.set_text_bg_color(color)
        return self

    def set_font(self, font_name=None, force=False):
        super().set_font(font_name, force)
        self.text_widget.set_font(font_name, force=True)
        self.dirty_shape = True
        return self

from __future__ import annotations
import pygame
import batFramework as bf
from .textRenderer import TextRenderer, PlainTextRenderer
from .textStyle import TextStyle
from typing import Callable, Self


class TextMixin:
    """
    Mixin for any widget that owns a single piece of rendered text.
    Provides all font management, text styling, outline, scroll,
    and renderer state. Layout/paint responsibilities stay in the
    concrete class.

    MRO note: place TextMixin before Shape/Widget in the class definition
    so that super().__init__(**kwargs) threads correctly through the chain.

        class Label(TextMixin, Shape): ...
    """

    def __init__(
        self,
        text: str = "",
        renderer: TextRenderer | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        # ---- Content --------------------------------------------
        self.text: str = text

        # ---- Font -----------------------------------------------
        self.font_size: int = bf.FontManager().DEFAULT_FONT_SIZE
        self.font_name: str | None = None
        self.font: pygame.font.Font = bf.FontManager().get_font(
            self.font_name, self.font_size
        )

        # ---- Text appearance ------------------------------------
        self.text_color: pygame.typing.ColorLike = "black"
        self.text_bg_color: pygame.typing.ColorLike | None = None
        self.bold: bool = False
        self.italic: bool = False
        self.underline: bool = False
        self.antialias: bool = bf.FontManager().DEFAULT_ANTIALIAS
        self.wraplength: int = 0

        # Controls wraplength from the widget's own inner width
        self.auto_wraplength: bool = False

        # pygame.FONT_LEFT / FONT_CENTER / FONT_RIGHT
        # (per-line alignment within a multiline block)
        self.line_alignment: int = pygame.FONT_LEFT

        # ---- Outline --------------------------------------------
        self.show_text_outline: bool = False
        self.text_outline_color: pygame.typing.ColorLike = "gray50"
        # Default 3×3 fully-filled convolution kernel
        self.text_outline_mask: pygame.Mask = pygame.Mask((3, 3), fill=True)

        # ---- Scroll ---------------------------------------------
        self.text_scroll: pygame.Vector2 = pygame.Vector2(0, 0)

        # ---- Renderer -------------------------------------------
        self.renderer: TextRenderer = renderer or PlainTextRenderer()


        self.filter_function: Callable[[str], str] | None = None
        

    # ==============================================================
    # Font management
    # ==============================================================

    def set_font_size(self, size: int) -> Self:
        if self.font_size != size:
            self.font_size = size
            self.font = bf.FontManager().get_font(self.font_name, self.font_size)
            self.dirty_shape = True
        return self

    def get_font_size(self) -> int:
        return self.font_size

    def set_font(self, name: str | None) -> Self:
        if self.font_name != name:
            self.font_name = name
            self.font = bf.FontManager().get_font(self.font_name, self.font_size)
            self.dirty_shape = True
        return self

    def get_font_name(self) -> str | None:
        return self.font_name

    # ==============================================================
    # Text content
    # ==============================================================

    def set_text(self, text: str) -> Self:
        raw = text
        text = self.filter_function(raw) if self.filter_function else raw
        if self.text != text:
            self.text = text
            self.dirty_shape = True
        return self

    def get_text(self) -> str:
        return self.text

    def set_filter(self, func: Callable[[str], str] | None) -> Self:
        self.filter_function = func
        return self

    # ==============================================================
    # Text colour / background
    # ==============================================================

    def set_text_color(self, color: pygame.typing.ColorLike) -> Self:
        if self.text_color != color:
            self.text_color = color
            self.dirty_surface = True
        return self

    def get_text_color(self) -> pygame.typing.ColorLike:
        return self.text_color

    def set_text_bg_color(self, color: pygame.typing.ColorLike | None) -> Self:
        if self.text_bg_color != color:
            self.text_bg_color = color
            # Propagate alpha requirement to the underlying surface when the
            # background is transparent/None (Widget/Drawable must expose this).
            is_transparent = color in (None, bf.color.TRANSPARENT)
            if hasattr(self, "set_convert_alpha"):
                self.set_convert_alpha(is_transparent)
            self.dirty_surface = True
        return self

    def get_text_bg_color(self) -> pygame.typing.ColorLike | None:
        return self.text_bg_color

    # ==============================================================
    # Font style flags
    # ==============================================================

    def set_bold(self, value: bool) -> Self:
        if self.bold != value:
            self.bold = value
            self.dirty_shape = True
        return self

    def is_bold(self) -> bool:
        return self.bold

    def set_italic(self, value: bool) -> Self:
        if self.italic != value:
            self.italic = value
            self.dirty_shape = True
        return self

    def is_italic(self) -> bool:
        return self.italic

    def set_underline(self, value: bool) -> Self:
        if self.underline != value:
            self.underline = value
            self.dirty_shape = True
        return self

    def is_underline(self) -> bool:
        return self.underline

    def set_antialias(self, value: bool) -> Self:
        if self.antialias != value:
            self.antialias = value
            self.dirty_surface = True
        return self

    def get_antialias(self) -> bool:
        return self.antialias

    # ==============================================================
    # Wraplength
    # ==============================================================

    def set_wraplength(self, value: int) -> Self:
        """Explicit pixel wraplength. Set to 0 to disable."""
        if self.wraplength != value:
            self.wraplength = value
            self.dirty_shape = True
        return self

    def get_wraplength(self) -> int:
        return self.wraplength

    def set_auto_wraplength(self, value: bool) -> Self:
        """
        When True the wraplength is derived automatically from the widget's
        current inner width each time the text is measured.
        """
        if self.auto_wraplength != value:
            self.auto_wraplength = value
            self.dirty_shape = True
        return self

    def _get_effective_wraplength(self) -> int:
        """
        Returns the wraplength that should be passed to the renderer.
        Respects auto_wraplength, but only when the widget is not set to
        auto-resize horizontally (otherwise wrapping would fight expansion).
        """
        if self.auto_wraplength and not self.autoresize_w:
            return int(self.get_inner_width())
        return self.wraplength

    # ==============================================================
    # Line alignment (within a multiline block)
    # ==============================================================

    def set_line_alignment(self, alignment: int) -> Self:
        """
        Per-line text alignment inside a multiline render.
        Accepts pygame.FONT_LEFT / FONT_CENTER / FONT_RIGHT.
        This is distinct from the widget's own alignment attribute.
        """
        if self.line_alignment != alignment:
            self.line_alignment = alignment
            self.dirty_surface = True
        return self

    def get_line_alignment(self) -> int:
        return self.line_alignment

    # ==============================================================
    # Outline
    # ==============================================================

    def set_show_text_outline(self, value: bool) -> Self:
        if self.show_text_outline != value:
            self.show_text_outline = value
            self.dirty_shape = True
        return self

    def set_text_outline_color(self, color: pygame.typing.ColorLike) -> Self:
        if self.text_outline_color != color:
            self.text_outline_color = color
            self.dirty_surface = True
        return self

    def get_text_outline_color(self) -> pygame.typing.ColorLike:
        return self.text_outline_color

    def set_text_outline_mask_size(self, size: tuple[int, int]) -> Self:
        """
        Resize the convolution mask, preserving bits that fit in the new size.
        """
        old = self.text_outline_mask
        old_w, old_h = old.get_size()
        min_w = min(old_w, size[0])
        min_h = min(old_h, size[1])
        preserved = [[old.get_at((x, y)) for x in range(min_w)] for y in range(min_h)]
        self.text_outline_mask = pygame.Mask(size, fill=False)
        self.set_text_outline_matrix(preserved)
        return self

    def set_text_outline_matrix(self, matrix: list[list[int]] | None) -> Self:
        """
        Set the convolution kernel from a 2-D list of 0/1 values.
        The matrix is stored in display order (row 0 = top), but the mask
        is filled with the y-axis flipped to match pygame's convention.
        Pass None to reset to all-zeros.
        """
        mw, mh = self.text_outline_mask.get_size()
        if matrix is None:
            matrix = [[0] * mw for _ in range(mh)]
        for y in range(mh):
            for x in range(mw):
                try:
                    self.text_outline_mask.set_at(
                        (x, y), matrix[mh - 1 - y][mw - 1 - x]
                    )
                except IndexError:
                    pass
        self.dirty_shape = True
        return self

    def _get_outline_offset(self) -> tuple[int, int]:
        """Half the mask size — used to centre the convolved outline."""
        mw, mh = self.text_outline_mask.get_size()
        return mw // 2, mh // 2

    # ==============================================================
    # Scroll
    # ==============================================================

    def set_scroll(self, x: float | None = None, y: float | None = None) -> Self:
        x = x if x is not None else self.text_scroll.x
        y = y if y is not None else self.text_scroll.y
        if self.text_scroll.x != x or self.text_scroll.y != y:
            self.text_scroll.update(x, y)
            self.dirty_surface = True
        return self

    def scroll_by(self, x: float = 0, y: float = 0) -> Self:
        if x or y:
            self.text_scroll += x, y
            self.dirty_surface = True
        return self

    # ==============================================================
    # Renderer
    # ==============================================================

    def set_renderer(self, renderer: TextRenderer) -> Self:
        if self.renderer is not renderer:
            self.renderer = renderer
            self.dirty_shape = True
        return self

    def get_renderer(self) -> TextRenderer:
        return self.renderer

    # ==============================================================
    # Style builder & size helper
    # ==============================================================

    def _build_style(self) -> TextStyle:
        return TextStyle(
            text=self.text,
            font=self.font,
            color=self.text_color,
            bg_color=self.text_bg_color,
            bold=self.bold,
            italic=self.italic,
            underline=self.underline,
            antialias=self.antialias,
            wraplength=self._get_effective_wraplength(),
            text_outline_mask=(
                self.text_outline_mask if self.show_text_outline else None
            ),
            text_outline_color=self.text_outline_color,
        )

    def get_text_size(self) -> tuple[int, int]:
        """Measured size of the rendered text, respecting the current style."""
        return self.renderer.get_min_size(self._build_style())

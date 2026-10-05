from __future__ import annotations
from math import ceil
import pygame
import batFramework as bf
from .shape import Shape
from .textMixin import TextMixin
from .textRenderer import TextRenderer
from .textEffects import TextEffect
from typing import Self


class Label(TextMixin, Shape):
    """
    A Shape that renders a single block of text.
    TextMixin owns all font/style/outline/scroll state.
    Shape owns background, border, relief painting.
    This class only adds alignment and ties both together.

    MRO: Label → TextMixin → Shape → Widget
    super().__init__() threads kwargs through the whole chain,
    """

    def __init__(self, text: str = "", renderer: TextRenderer | None = None):
        super().__init__(text=text, renderer=renderer)
        self.alignment: bf.alignment = bf.alignment.CENTER
        # Blit position in local surface coordinates, updated during arrangement.
        self.text_rect = pygame.FRect(0, 0, 0, 0)
        self.text_effect: TextEffect | None = None
        self.set_surface_flags(pygame.SRCALPHA)
        self.set_convert_alpha(True)
        self.set_autoresize(True)
    def __str__(self) -> str:
        return f"Label({repr(self.text)})"

    # ------------------------------------------------------------------
    # Text effect
    # ------------------------------------------------------------------

    def set_text_effect(self, effect: TextEffect | None) -> Self:
        self.text_effect = effect
        self.dirty_surface = True
        self.mark_shape_dirty()
        return self

    # ------------------------------------------------------------------
    # Alignment
    # ------------------------------------------------------------------

    def set_alignment(self, alignment: bf.alignment) -> Self:
        if self.alignment != alignment:
            self.alignment = alignment
            self.dirty_surface = True
        return self

    def get_alignment(self) -> bf.alignment:
        return self.alignment

    # ------------------------------------------------------------------
    # Sizing
    # ------------------------------------------------------------------

    def get_min_required_size(self) -> tuple[float, float]:
        tw, th = self.get_text_size()
        r =  self.expand_rect_with_padding((0, 0, tw, th)).size
        return self.compute_min_size(r)

    # ------------------------------------------------------------------
    # Arrangement (text offset, no drawing)
    # ------------------------------------------------------------------

    def arrange_override(self):
        self._recompute_text_rect()
        super().arrange_override()

    def _align_text_helper(self,text_rect):
        inner = self.get_local_inner_rect()

        # Align text_rect to inner rect using pygame's rect API
        anchor = self.alignment.value
        if hasattr(inner, anchor):
            setattr(text_rect, anchor, getattr(inner, anchor))
        else:
            text_rect.topleft = inner.topleft

        text_rect.topleft = (
            ceil(text_rect.left),
            ceil(text_rect.top),
        )

    def _recompute_text_rect(self) -> None:
        tw, th = self.get_text_size()

        # Rect representing the text block
        self.text_rect.update(0, 0, tw, th)
        self._align_text_helper(self.text_rect)



    # ------------------------------------------------------------------
    # Paint
    # ------------------------------------------------------------------

    def _build_style(self):
        if self.text_effect:
            # Temporarily swap self.text so the parent builds the style
            # with the effect-transformed string, then restore immediately.
            raw = self.text
            self.text = self.text_effect.apply(raw)
            style = super()._build_style()
            self.text = raw
            return style
        return super()._build_style()

    def needs_paint(self) -> bool:
        return self.visible and bool(
            self.dirty_surface or self.renderer.DYNAMIC
            or (self.text_effect and self.text_effect.DYNAMIC)
        )

    def paint(self) -> None:
        # Shape draws background fill, relief shadow, and border outline.
        super().paint()
        text_surf = self.renderer.render(self._build_style())
        old_clip = self.surface.get_clip()
        self.surface.set_clip(self.get_local_inner_rect())
        self.surface.blit(
            text_surf, self.text_rect.move(-self.text_scroll.x, -self.text_scroll.y).topleft
        )
        self.surface.set_clip(old_clip)
        
    def get_debug_outlines(self):
        if not self.visible:
            return
        yield from super().get_debug_outlines()
        if self.text:
            yield self.text_rect.move(*self.rect.topleft).move(
                -self.text_scroll.x, -self.text_scroll.y
            ), "purple"

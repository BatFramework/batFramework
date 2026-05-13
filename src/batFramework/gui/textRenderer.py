from .textStyle import TextStyle
import pygame
import re
import math
from collections import OrderedDict

TAG_PATTERN = re.compile(r"(\\[\\[])|\[(\/?)(\w+)(?:=([^\]]+))?\]")


def _min_size_key(style: TextStyle) -> tuple:
    """Hashable key from the style fields that affect text layout/size."""
    return (
        style.text,
        id(style.font),
        style.bold,
        style.italic,
        style.underline,
        style.wraplength,
        id(style.text_outline_mask) if style.text_outline_mask else None,
    )


def _cache_min_size(max_size: int = 64):
    """Per-instance LRU cache for get_min_size, keyed on the text style."""
    def decorator(method):
        _method_key = method.__qualname__
        def wrapper(self, style):
            try:
                cache = self._min_size_cache
            except AttributeError:
                cache = OrderedDict()
                self._min_size_cache = cache
            key = (_method_key, _min_size_key(style))
            if key in cache:
                cache.move_to_end(key)
                return cache[key]
            result = method(self, style)
            cache[key] = result
            if len(cache) > max_size:
                cache.popitem(last=False)
            return result
        wrapper.__name__ = method.__name__
        wrapper.__qualname__ = method.__qualname__
        return wrapper
    return decorator


class TextRenderer:
    DYNAMIC = False

    def get_min_size(self, style: TextStyle) -> tuple[int, int]:
        raise NotImplementedError

    def render(self, style: TextStyle) -> pygame.Surface:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# PlainTextRenderer
# ---------------------------------------------------------------------------

class PlainTextRenderer(TextRenderer):

    def __init__(self):
        self._empty_surface: pygame.Surface | None = None

    def _get_empty(self, font: pygame.font.Font, outline_mask=None) -> pygame.Surface:
        """Return a cached minimal transparent surface for empty text."""
        if self._empty_surface is None:
            h = font.get_height()
            w = 1
            if outline_mask:
                off = outline_mask.get_size()[0] // 2
                w += off * 2
                h += off * 2
            self._empty_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        return self._empty_surface

    def _apply_font_style(self, font: pygame.font.Font, style: TextStyle):
        font.set_bold(style.bold)
        font.set_italic(style.italic)
        font.set_underline(style.underline)

    def _wrap_lines(self, text: str, font: pygame.font.Font, wraplength: int):
        if not wraplength:
            return text.split("\n")

        lines = []
        for raw_line in text.split("\n"):
            words = raw_line.split(" ")
            current = ""
            for word in words:
                test = current + (" " if current else "") + word
                if font.size(test)[0] <= wraplength:
                    current = test
                else:
                    if current:
                        lines.append(current)
                    current = word
            lines.append(current)

        return lines

    @_cache_min_size()
    def get_min_size(self, style: TextStyle):
        font = style.font
        self._apply_font_style(font, style)

        lines = self._wrap_lines(style.text, font, style.wraplength)

        max_w = 0
        total_h = 0

        for line in lines:
            w, h = font.size(line if line else " ")
            max_w = max(max_w, w)
            total_h += h

        if style.text_outline_mask:
            off = style.text_outline_mask.get_size()[0] // 2
            max_w += off * 2
            total_h += off * 2

        if total_h == 0:
            total_h = font.get_height()
        return max_w, total_h

    def render(self, style: TextStyle):
        font = style.font
        self._apply_font_style(font, style)

        if not style.text:
            return self._get_empty(font, style.text_outline_mask)

        lines = self._wrap_lines(style.text, font, style.wraplength)
        line_surfaces: list[pygame.Surface] = []
        max_w = 0
        total_h = 0

        for line in lines:
            surf = font.render(line if line else " ", style.antialias, style.color)

            if style.text_outline_mask:
                mask = pygame.mask.from_surface(surf).convolve(style.text_outline_mask)
                text_outline = mask.to_surface(
                    setcolor=style.text_outline_color, unsetcolor=(0, 0, 0, 0)
                )
                offset = style.text_outline_mask.get_size()[0] // 2
                text_outline.blit(surf, (offset, offset))
                surf = text_outline

            line_surfaces.append(surf)
            max_w = max(max_w, surf.get_width())
            total_h += surf.get_height()

        surface = pygame.Surface((max_w, total_h), pygame.SRCALPHA)
        y = 0
        for surf in line_surfaces:
            surface.blit(surf, (0, y))
            y += surf.get_height()

        return surface


# ---------------------------------------------------------------------------
# RichTextRenderer
# ---------------------------------------------------------------------------

class RichTextRenderer(TextRenderer):

    def __init__(self):
        self._empty_surface: pygame.Surface | None = None

    def _get_empty(self, font: pygame.font.Font) -> pygame.Surface:
        if self._empty_surface is None:
            self._empty_surface = pygame.Surface((1, font.get_height()), pygame.SRCALPHA)
        return self._empty_surface

    def _parse(self, text):
        pos = 0
        stack = [(None, {})]
        segments = []

        def _compute_current_state():
            state = {}
            for tag_name, props in stack:
                state.update(props)
            return state

        for m in TAG_PATTERN.finditer(text):
            start, end = m.span()

            if start > pos:
                segments.append((text[pos:start], _compute_current_state()))

            closing, tag, value = m.groups()

            if not closing:
                props = {}
                if tag == "b":
                    props["bold"] = True
                elif tag == "i":
                    props["italic"] = True
                elif tag == "u":
                    props["underline"] = True
                elif tag == "color":
                    try:
                        props["color"] = pygame.Color(value)
                    except (ValueError, TypeError):
                        props["color"] = pygame.Color(0, 0, 0)
                stack.append((tag, props))
            else:
                for i in range(len(stack) - 1, 0, -1):
                    if stack[i][0] == tag:
                        stack.pop(i)
                        break

            pos = end

        if pos < len(text):
            segments.append((text[pos:], _compute_current_state()))

        return segments

    @_cache_min_size()
    def get_min_size(self, style: TextStyle):
        surface = self.render(style)
        return surface.get_size()

    def render(self, style: TextStyle):
        font = style.font

        if not style.text:
            return self._get_empty(font)

        segments = self._parse(style.text)

        current_line = []
        max_line_height = 0
        lines = []

        for text, override in segments:
            parts = text.split("\n")
            for i, part in enumerate(parts):
                font.set_bold(override.get("bold", style.bold))
                font.set_italic(override.get("italic", style.italic))
                font.set_underline(override.get("underline", style.underline))
                color = override.get("color", style.color)

                surf = font.render(part if part else " ", style.antialias, color)
                current_line.append(surf)
                max_line_height = max(max_line_height, surf.get_height())

                if i < len(parts) - 1:
                    lines.append((current_line, max_line_height))
                    current_line = []
                    max_line_height = 0

        lines.append((current_line, max_line_height))

        total_w = 0
        total_h = 0
        for line, h in lines:
            w = sum(s.get_width() for s in line)
            total_w = max(total_w, w)
            total_h += h

        if total_h == 0:
            total_h = font.get_height()
        if total_w == 0:
            total_w = 1

        surface = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
        y = 0
        for line, h in lines:
            x = 0
            for surf in line:
                surface.blit(surf, (x, y))
                x += surf.get_width()
            y += h

        return surface


# ---------------------------------------------------------------------------
# WaveTextRenderer
# ---------------------------------------------------------------------------

class WaveTextRenderer(RichTextRenderer):
    DYNAMIC = True
    """
    Renders text with a per-character vertical sine-wave offset.
    Inherits tag parsing from RichTextRenderer so [color], [b], [i], [u]
    tags all work transparently alongside the wave effect.

    The rendered surface is cached and only recomputed when the text/style
    changes or the wave has visually advanced by at least one step.
    Step duration is derived from `speed`: step_ms = 1000 / (60 * speed).

    Parameters
    ----------
    amplitude   Peak vertical displacement in pixels from the baseline.
    frequency   Number of full wave cycles spread across the whole string.
    phase       Starting phase in radians.
    speed       Animation speed multiplier (1.0 = 60 steps/sec).
    """

    def __init__(
        self,
        amplitude: float = 4.0,
        frequency: float = 1.0,
        phase: float = 0.0,
        speed: float = 1.0,
    ):
        super().__init__()
        self.amplitude = amplitude
        self.frequency = frequency
        self.phase = phase
        self.speed = speed

        # Rolling cache: OrderedDict keyed on (style_key, time_bucket).
        # Capped at _CACHE_SIZE to bound memory — oldest entry evicted first.
        self._cache: OrderedDict[tuple, pygame.Surface] = OrderedDict()
        self._empty_wave: pygame.Surface | None = None

    _CACHE_SIZE: int = 3  # keep at most 3 rendered buckets
    _STEP_MS = 16

    def _time_bucket(self) -> int:
        """Quantise time so the cache is stable within one visual step."""
        effective_step = max(1, int(self._STEP_MS / max(self.speed, 0.001)))
        return pygame.time.get_ticks() // effective_step

    def _style_key(self, style: TextStyle) -> tuple:
        return (
            style.text,
            id(style.font),
            style.bold, style.italic, style.underline,
            style.antialias,
            style.color if not hasattr(style.color, '__iter__')
            else tuple(style.color),
        )

    def _get_empty_wave(self, font: pygame.font.Font) -> pygame.Surface:
        if self._empty_wave is None:
            amp = int(math.ceil(self.amplitude))
            total_h = font.get_height() + amp * 2
            self._empty_wave = pygame.Surface((1, total_h), pygame.SRCALPHA)
        return self._empty_wave

    def _char_y_offset(self, char_index: int, total_chars: int) -> int:
        t = char_index / max(total_chars - 1, 1)
        time_phase = pygame.time.get_ticks() / 1000.0 * self.speed
        return int(round(
            self.amplitude * math.sin(2 * math.pi * self.frequency * t + self.phase + time_phase)
        ))

    @_cache_min_size()
    def get_min_size(self, style: TextStyle) -> tuple[int, int]:
        w, h = super().get_min_size(style)
        extra = int(math.ceil(self.amplitude)) * 2
        return w, h + extra

    def render(self, style: TextStyle) -> pygame.Surface:
        font = style.font

        if not style.text:
            return self._get_empty_wave(font)

        # Rolling cache lookup
        key = (self._style_key(style), self._time_bucket())
        if key in self._cache:
            # Move to end (most-recently-used) and return
            self._cache.move_to_end(key)
            return self._cache[key]

        segments = self._parse(style.text)

        char_overrides: list[tuple[str, dict]] = [
            (ch, override)
            for text, override in segments
            for ch in text
        ]

        total_chars = len(char_overrides)
        amp = int(math.ceil(self.amplitude))

        char_surfs: list[tuple[pygame.Surface, int]] = []
        total_w = 0
        base_h = 0

        for i, (ch, override) in enumerate(char_overrides):
            font.set_bold(override.get("bold", style.bold))
            font.set_italic(override.get("italic", style.italic))
            font.set_underline(override.get("underline", style.underline))
            color = override.get("color", style.color)

            surf = font.render(ch if ch.strip() else " ", style.antialias, color)
            y_off = self._char_y_offset(i, total_chars)
            char_surfs.append((surf, y_off))
            total_w += surf.get_width()
            base_h = max(base_h, surf.get_height())

        if base_h == 0:
            base_h = font.get_height()

        total_h = base_h + amp * 2
        surface = pygame.Surface((max(total_w, 1), total_h), pygame.SRCALPHA)

        x = 0
        for surf, y_off in char_surfs:
            surface.blit(surf, (x, amp + y_off))
            x += surf.get_width()

        self._cache[key] = surface
        if len(self._cache) > self._CACHE_SIZE:
            self._cache.popitem(last=False)  # evict oldest
        return surface
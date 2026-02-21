"""
textEffects.py
~~~~~~~~~~~~~~
Class-based text-level effects for use with RichTextRenderer.

Every effect exposes:
    DYNAMIC: bool           — True → Label marks dirty_surface each frame
    apply(text: str) -> str — returns a tagged display string

Dynamic effects are time-gated: apply() recomputes only when at least
`speed` milliseconds have elapsed since the last step, OR when the
source text has changed. Between steps the cached result is returned
immediately, so DYNAMIC effects have zero per-frame cost at rest.

Usage
-----
    label.set_text_effect(RainbowEffect(speed=50))
    label.set_text_effect(None)  # clear
"""

from __future__ import annotations
import colorsys
import pygame
from typing import ClassVar


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class TextEffect:
    DYNAMIC: ClassVar[bool] = False

    def apply(self, text: str) -> str:
        raise NotImplementedError


class DynamicTextEffect(TextEffect):
    """
    Base for animated effects. Handles the time-gate and result cache so
    subclasses only implement _compute(text) and _advance_offset(text).

    apply() recomputes only when:
      - the source text has changed, OR
      - at least `speed` ms have elapsed since the last step
    Otherwise it returns the cached string immediately.
    """
    DYNAMIC = True

    def __init__(self, speed: int = 50):
        """
        Parameters
        ----------
        speed   Minimum milliseconds between animation steps.
                Lower = faster. e.g. 50 ms ≈ 20 steps/sec.
        """
        self.speed: int = speed
        self._last_ticks: int = 0
        self._cached_text: str | None = None
        self._cached_result: str = ""

    def apply(self, text: str) -> str:
        now = pygame.time.get_ticks()
        text_changed = text != self._cached_text
        elapsed = now - self._last_ticks

        if not text_changed and elapsed < self.speed:
            return self._cached_result

        if elapsed >= self.speed:
            self._advance_offset(text)
            self._last_ticks = now

        self._cached_text = text
        self._cached_result = self._compute(text)
        return self._cached_result

    def _advance_offset(self, text: str) -> None:
        raise NotImplementedError

    def _compute(self, text: str) -> str:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hsv_to_hex(h: float, s: float = 1.0, v: float = 1.0) -> str:
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"


def _visible_indices(text: str) -> list[int]:
    return [i for i, ch in enumerate(text) if ch.strip()]


# ---------------------------------------------------------------------------
# Rainbow
# ---------------------------------------------------------------------------

class RainbowEffect(DynamicTextEffect):
    """Sliding per-character rainbow. Hue band shifts on every time step."""

    def __init__(
        self,
        speed: int = 50,
        steps_per_tick: int = 1,
        saturation: float = 1.0,
        value: float = 1.0,
    ):
        super().__init__(speed)
        self.steps_per_tick = steps_per_tick
        self.saturation = saturation
        self.value = value
        self._offset = 0

    def _advance_offset(self, text: str) -> None:
        n = max(len(_visible_indices(text)), 1)
        self._offset = (self._offset + self.steps_per_tick) % n

    def _compute(self, text: str) -> str:
        visible = _visible_indices(text)
        n = max(len(visible), 1)
        vis_rank = {idx: rank for rank, idx in enumerate(visible)}
        parts: list[str] = []
        for i, ch in enumerate(text):
            if i not in vis_rank:
                parts.append(ch)
                continue
            hue = (vis_rank[i] - self._offset) / n
            parts.append(f"[color={_hsv_to_hex(hue, self.saturation, self.value)}]{ch}[/color]")
        return "".join(parts)


# ---------------------------------------------------------------------------
# Gradient
# ---------------------------------------------------------------------------

class GradientEffect(DynamicTextEffect):
    """Sliding two-colour linear gradient."""

    def __init__(
        self,
        color_a: tuple[int, int, int],
        color_b: tuple[int, int, int],
        speed: int = 50,
        steps_per_tick: int = 1,
    ):
        super().__init__(speed)
        self.color_a = color_a
        self.color_b = color_b
        self.steps_per_tick = steps_per_tick
        self._offset = 0

    def _lerp(self, t: float) -> str:
        r = int(self.color_a[0] + (self.color_b[0] - self.color_a[0]) * t)
        g = int(self.color_a[1] + (self.color_b[1] - self.color_a[1]) * t)
        b = int(self.color_a[2] + (self.color_b[2] - self.color_a[2]) * t)
        return f"#{r:02X}{g:02X}{b:02X}"

    def _advance_offset(self, text: str) -> None:
        n = max(len(_visible_indices(text)), 1)
        self._offset = (self._offset + self.steps_per_tick) % n

    def _compute(self, text: str) -> str:
        visible = _visible_indices(text)
        n = max(len(visible), 1)
        vis_rank = {idx: rank for rank, idx in enumerate(visible)}
        parts: list[str] = []
        for i, ch in enumerate(text):
            if i not in vis_rank:
                parts.append(ch)
                continue
            t = ((vis_rank[i] - self._offset) % n) / n
            parts.append(f"[color={self._lerp(t)}]{ch}[/color]")
        return "".join(parts)


# ---------------------------------------------------------------------------
# Static tint — non-dynamic, no caching needed
# ---------------------------------------------------------------------------

class TintEffect(TextEffect):
    """Wraps every non-whitespace character in a single fixed colour tag."""

    DYNAMIC = False

    def __init__(self, color: pygame.typing.ColorLike):
        self.color = pygame.Color(color) if not isinstance(color,pygame.Color) else color 

    def apply(self, text: str) -> str:
        parts: list[str] = []
        for ch in text:
            if not ch.strip():
                parts.append(ch)
            else:
                parts.append(f"[color={self.color.hex}]{ch}[/color]")
        return "".join(parts)
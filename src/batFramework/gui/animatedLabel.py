from .label import Label
from .textRenderer import RichTextRenderer, TAG_PATTERN
import batFramework as bf
from typing import Self, Callable, Any
from .label import Label
from .textRenderer import RichTextRenderer, TAG_PATTERN
import batFramework as bf
from typing import Self, Callable, Any


class AnimatedLabel(Label):
    def __init__(self, text: str = "") -> None:
        self.cursor_position: float = 0.0
        self.timer = bf.Timer(1, self._animate_text, -1).start()
        self.original_text: str = ""
        self.end_callback: Callable[[], Any] | None = None

        # Maps visible-char index -> string index of that char's exclusive end.
        # None when the renderer is not a RichTextRenderer.
        self._char_map: list[int] | None = None

        # Prevents end_callback from firing multiple times for the same text.
        self._ended: bool = False

        super().__init__("")
        self.set_alignment(bf.alignment.TOPLEFT)
        self.set_text(text)

    def __str__(self) -> str:
        return "AnimatedLabel"

    # ------------------------------------------------------------
    # Rich-text char map
    # ------------------------------------------------------------

    def _build_char_map(self, text: str) -> list[int] | None:
        """
        If the current renderer understands tags, return a list where
        entry[i] is the string index (exclusive end) for the i-th visible
        character. Tag spans are skipped entirely so the cursor only counts
        real glyphs. Returns None for plain renderers.
        """
        if not isinstance(self.renderer, RichTextRenderer):
            return None

        tag_spans: dict[int, int] = {
            m.start(): m.end() for m in TAG_PATTERN.finditer(text)
        }

        char_map: list[int] = []
        i = 0

        while i < len(text):
            if i in tag_spans:
                i = tag_spans[i]
            else:
                char_map.append(i + 1)
                i += 1

        return char_map

    def _visible_char_count(self) -> int:
        """Total number of animatable characters in the current text."""
        if self._char_map is not None:
            return len(self._char_map)
        return len(self.original_text)

    def _slice_text(self, n: int) -> str:
        """Return original_text sliced to show the first n visible chars."""
        if n <= 0:
            return ""

        if self._char_map is not None:
            if n >= len(self._char_map):
                return self.original_text
            return self.original_text[: self._char_map[n - 1]]

        return self.original_text[:n]

    def _finish(self) -> None:
        """Reveal all text, stop animation, and fire the end callback once."""
        self.cursor_position = self._visible_char_count()
        self._update_visible_text()
        self.timer.stop()

        if not self._ended:
            self._ended = True
            if self.end_callback:
                self.end_callback()

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------

    def set_end_callback(self, callback: Callable[[], Any] | None) -> Self:
        self.end_callback = callback

        # If the label already finished before the callback was assigned,
        # fire it immediately so late callback assignment still works.
        if self._ended and self.end_callback:
            self.end_callback()

        return self

    def pause(self) -> Self:
        self.timer.pause()
        return self

    def resume(self) -> Self:
        if self.cursor_position < self._visible_char_count():
            self.timer.resume()
        return self

    @property
    def text_speed(self) -> float:
        return self.timer.duration

    @text_speed.setter
    def text_speed(self, speed: float) -> None:
        self.timer.set_duration(speed)

    def set_text_speed(self, speed: float) -> Self:
        """
        Set the text animation speed in seconds per character.

        If speed is <= 0, the text appears immediately.
        If changed to <= 0 while already animating, the full text is revealed
        immediately and the end callback is fired once.
        """
        self.text_speed = speed

        if speed <= 0:
            self._finish()
        else:
            if self.cursor_position < self._visible_char_count():
                self.timer.start(force=True)

        return self

    def set_renderer(self, renderer) -> Self:
        super().set_renderer(renderer)

        self._char_map = self._build_char_map(self.original_text)

        # Preserve the currently visible character count after renderer changes.
        self._update_visible_text()

        return self

    # ------------------------------------------------------------
    # Text control
    # ------------------------------------------------------------

    def set_text(self, text: str) -> Self:
        self.original_text = text
        self._char_map = self._build_char_map(text)
        self.cursor_position = 0.0
        self._ended = False

        if self.text_speed > 0:
            self.timer.start(force=True)
            self._update_visible_text()
        else:
            self._finish()

        return self

    def _update_visible_text(self) -> None:
        visible = self._slice_text(int(self.cursor_position))
        super().set_text(visible)

    # ------------------------------------------------------------
    # Update loop
    # ------------------------------------------------------------

    def _animate_text(self) -> None:
        if self.timer.is_stopped or self.timer.is_paused:
            return

        total = self._visible_char_count()

        if total <= 0:
            self._finish()
            return

        self.cursor_position = min(self.cursor_position + 1, total)
        self._update_visible_text()

        if self.cursor_position >= total:
            self._finish()
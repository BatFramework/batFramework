from .label import Label
from .textRenderer import RichTextRenderer, TAG_PATTERN
import batFramework as bf
from typing import Self, Callable, Any


class AnimatedLabel(Label):
    def __init__(self, text: str = "") -> None:
        self.cursor_position: float = 0.0
        self.timer = bf.Timer(10, self._animate_text, -1).start()
        self.original_text: str = ""
        self.end_callback: Callable[[], Any] | None = None
        # Maps visible-char index → string index of that char's last byte.
        # None when the renderer is not a RichTextRenderer.
        self._char_map: list[int] | None = None

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
        character.  Tag spans are skipped entirely so the cursor only counts
        real glyphs.  Returns None for plain renderers.
        """
        if not isinstance(self.renderer, RichTextRenderer):
            return None

        # Build a fast lookup: start → end for every tag span.
        tag_spans: dict[int, int] = {
            m.start(): m.end() for m in TAG_PATTERN.finditer(text)
        }

        char_map: list[int] = []
        i = 0
        while i < len(text):
            if i in tag_spans:
                i = tag_spans[i]          # jump past the whole tag
            else:
                char_map.append(i + 1)    # exclusive end of this character
                i += 1

        return char_map

    def _visible_char_count(self) -> int:
        """Total number of animatable characters in the current text."""
        if self._char_map is not None:
            return len(self._char_map)
        return len(self.original_text)

    def _slice_text(self, n: int) -> str:
        """Return original_text sliced to show the first `n` visible chars."""
        if n <= 0:
            return ""
        if self._char_map is not None:
            if n >= len(self._char_map):
                return self.original_text
            return self.original_text[: self._char_map[n - 1]]
        return self.original_text[:n]

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------

    def set_end_callback(self, callback: Callable[[], Any]) -> Self:
        self.end_callback = callback
        return self

    def pause(self) -> Self:
        self.timer.pause()
        return self

    def resume(self) -> Self:
        self.timer.resume()
        return self

    @property
    def text_speed(self):
        return self.timer.duration

    @text_speed.setter
    def text_speed(self, speed):
        self.timer.set_duration(speed)

    def set_text_speed(self, speed: float) -> Self:
        """
        Set the text animation speed for the label.
        Args:
            speed (float): The speed at which text is animated. If speed is negative or 0,
                           the text is not animated and appears instantaneously.
        Returns:
            Self: Returns the instance itself for method chaining.
        """

        self.text_speed = speed
        return self

    def set_renderer(self, renderer) -> Self:
        super().set_renderer(renderer)
        # Rebuild char map if the renderer type changed.
        self._char_map = self._build_char_map(self.original_text)
        return self

    # ------------------------------------------------------------
    # Text control
    # ------------------------------------------------------------

    def set_text(self, text: str) -> Self:
        self.original_text = text
        if self.text_speed > 0:
            self.cursor_position = 0.0
            self._char_map = self._build_char_map(text)
            self.timer.start(force=True)
            self._update_visible_text()
        else:
            self.timer.pause()
            self._char_map = self._build_char_map(text)

            total = self._visible_char_count()
            self.cursor_position = total
            self._update_visible_text()
        return self

    def _update_visible_text(self) -> None:
        visible = self._slice_text(int(self.cursor_position))
        super().set_text(visible)
        self.dirty_shape = True

    # ------------------------------------------------------------
    # Update loop
    # ------------------------------------------------------------

    def _animate_text(self):
        if self.timer.is_stopped or self.timer.is_paused:
            return

        total = self._visible_char_count()
        self.cursor_position = min(self.cursor_position + 1, total)

        self._update_visible_text()

        if self.cursor_position >= total:
            self.timer.stop()
            if self.end_callback:
                self.end_callback()
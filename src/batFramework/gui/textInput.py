import pygame
import batFramework as bf
from typing import Callable, Any, Self
from .label import Label
from .interactiveWidget import InteractiveWidget
from .interactiveShape import InteractiveShape
from .textBuffer import TextBuffer
from .textRenderer import TextRenderer, PlainTextRenderer


class TextInput(Label, InteractiveShape):
    def __init__(self, text: str = "", renderer: TextRenderer | None = None):
        super().__init__(text="", renderer=renderer or PlainTextRenderer())
        self.set_alignment(bf.alignment.TOPLEFT)

        self.buffer = TextBuffer(text)
        self.set_text(self.buffer.get_text())

        self.cursor_visible: bool = False
        self.cursor_blink_rate: float = 0.2

        self.cursor_timer = bf.Timer(self.cursor_blink_rate, self._toggle_cursor, loop=-1).start()
        self.cursor_timer.pause()

        self.old_key_repeat: tuple[int, int] = (0, 0)
        self.set_click_pass_through(False)

        self.text_scroll.xy = (0, 0)
        self.edited_this_frame: bool = False

        self.set_padding((6, 4))
        self.set_autoresize(True)

    def __str__(self) -> str:
        return f"TextInput({repr(self.buffer.get_text())})"

    # =================================================
    # Cursor
    # =================================================

    def _toggle_cursor(self):
        self.cursor_visible = not self.cursor_visible
        self.dirty_surface = True

    def _reset_cursor_blink(self):
        """Restart the blink cycle from the visible phase.
        Only call this on focus gain — not on every keypress."""
        self.cursor_visible = True
        self.cursor_timer.start(force=True)
        self.dirty_surface = True

    def _show_cursor(self):
        """Make the cursor visible right now without disrupting the blink cadence.
        The timer keeps running at its natural pace; it will blink off at the next tick."""
        if not self.cursor_visible:
            self.cursor_visible = True
            self.dirty_surface = True

    # =================================================
    # Focus handling
    # =================================================

    def do_on_enter(self):
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_IBEAM)

    def do_on_exit(self):
        pygame.mouse.set_cursor(bf.const.DEFAULT_CURSOR)

    def do_on_get_focus(self):
        self.old_key_repeat = pygame.key.get_repeat()
        pygame.key.set_repeat(200, 50)
        self._reset_cursor_blink()

    def do_on_lose_focus(self):
        pygame.key.set_repeat(*self.old_key_repeat)
        self.cursor_visible = False
        self.cursor_timer.pause()
        self.dirty_surface = True

    def on_click_down(self, button, event=None):
        if button == 1:
            self.ask_focus()
            self._place_cursor_from_mouse()
        return super().on_click_down(button, event)

    # =================================================
    # Input handling
    # =================================================

    def handle_event(self, event):
        self.edited_this_frame = False
        super().handle_event(event)
        if event.consumed or not self.is_focused:
            return

        if event.type == pygame.TEXTINPUT:
            self.buffer.insert_char(event.text)
            self._after_edit()
            event.consumed = True
            return

        if event.type != pygame.KEYDOWN:
            return

        k = event.key

        if k == pygame.K_BACKSPACE:
            self.buffer.backspace()
        elif k == pygame.K_DELETE:
            self.buffer.delete()
        elif k == pygame.K_RETURN:
            self.buffer.insert_newline()
        elif k == pygame.K_LEFT:
            self.buffer.move_left()
        elif k == pygame.K_RIGHT:
            self.buffer.move_right()
        elif k == pygame.K_UP:
            self.buffer.move_up()
        elif k == pygame.K_DOWN:
            self.buffer.move_down()
        else:
            return

        self.edited_this_frame = True
        self._after_edit()
        event.consumed = True

    def _after_edit(self):
        self.set_text(self.buffer.get_text())
        self._show_cursor()        # visible now, blink timer untouched
        self.dirty_surface = True  # cursor position may have changed even if text/visibility didn't
        self.edited_this_frame = True

    # =================================================
    # Cursor helpers
    # =================================================

    def _get_cursor_pixel_rect(self) -> tuple[float, float, float]:
        font = self.font
        y = 0
        for i, line in enumerate(self.buffer.lines):
            h = font.get_height()
            if i == self.buffer.cursor_y:
                x = font.size(line[: self.buffer.cursor_x])[0]
                return x, y, h
            y += h
        return 0, 0, font.get_height()

    def _ensure_cursor_visible(self):
        cx, cy, ch = self._get_cursor_pixel_rect()
        inner = self.get_local_inner_rect()

        parent = self.parent
        parent_interactive = isinstance(parent, InteractiveWidget)

        new_sx = self.text_scroll.x
        new_sy = self.text_scroll.y

        delegate_x = parent_interactive and not parent.autoresize_w
        delegate_y = parent_interactive and not parent.autoresize_h

        if delegate_x and self.autoresize_w == self.parent.autoresize_w and self.autoresize_w == False:
            delegate_x = False
        if delegate_y and self.autoresize_h == self.parent.autoresize_h and self.autoresize_h == False:
            delegate_y = False

        if not delegate_x and not self.autoresize_w:
            if cx < new_sx:
                new_sx = cx
            elif cx > new_sx + inner.width:
                new_sx = cx - inner.width + 2

        if not delegate_y and not self.autoresize_h:
            if cy < new_sy:
                new_sy = cy
            elif cy + ch > new_sy + inner.height:
                new_sy = cy + ch - inner.height

        self.set_scroll(new_sx, new_sy)

        if delegate_x or delegate_y:
            inner_abs = self.get_inner_rect()
            caret_rect = pygame.Rect(
                inner_abs.left + cx - new_sx,
                inner_abs.top + cy - new_sy,
                2,
                ch,
            )
            parent.set_focused_child(self, caret_rect)

    def _place_cursor_from_mouse(self):
        if not self.parent_layer:
            return

        camera = self.parent_layer.camera
        mx, my = camera.get_mouse_pos()
        inner = self.get_inner_rect()

        x = mx - inner.left + self.text_scroll.x
        y = my - inner.top + self.text_scroll.y

        font = self.font
        line_h = font.get_height()

        line_index = int(y // line_h)
        line_index = max(0, min(line_index, len(self.buffer.lines) - 1))

        line = self.buffer.lines[line_index]
        cx = 0
        char_index = 0
        for i, ch in enumerate(line):
            w = font.size(ch)[0]
            if cx + w / 2 >= x:
                char_index = i
                break
            cx += w
            char_index = i + 1

        self.buffer.cursor_x = char_index
        self.buffer.cursor_y = line_index
        self._after_edit()

    # =================================================
    # Callback
    # =================================================

    def set_modify_callback(self, callback: Callable[[str], Any]) -> Self:
        self.buffer.set_callback(callback)
        return self

    def set_filter(self, func: Callable[[str], str] | None) -> Self:
        super().set_filter(func)
        self._after_edit()
        return self

    def build(self) -> bool:
        target = self.resolve_size(self.get_min_required_size())
        changed = self.rect.size != target
        if changed:
            self.set_size(target)
        self._recompute_text_rect()
        return changed

    def apply_post_updates(self, skip_draw=False):
        super().apply_post_updates(skip_draw)
        if self.edited_this_frame:
            self._ensure_cursor_visible()
            self.edited_this_frame = False

    # =================================================
    # Paint
    # =================================================

    def paint(self) -> None:
        super().paint()
        if not self.cursor_visible:
            return

        cx, cy, ch = self._get_cursor_pixel_rect()
        inner = self.get_local_inner_rect()

        pygame.draw.rect(
            self.surface,
            self.text_color,
            pygame.Rect(
                inner.left + cx - self.text_scroll.x,
                inner.top + cy - self.text_scroll.y,
                2,
                ch,
            ),
        )
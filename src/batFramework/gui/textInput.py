import batFramework as bf
from typing import Self
from .label import Label
from .interactiveWidget import InteractiveWidget
import pygame


class TextInput(Label, InteractiveWidget):
    def __init__(self) -> None:
        self.cursor_position = 0
        super().__init__("A")
        self.set_text("")
        self.set_focusable(True)
        self.set_outline_color("black")
        self.old_key_repeat: tuple = (0, 0)
        self.cursor_timer = bf.Timer(0.3, self._cursor_toggle, loop=True).start()
        self.cursor_timer.pause()
        self.show_cursor: bool = True

    def to_string_id(self) -> str:
        return f"TextInput({self.text})"

    def _cursor_toggle(self):
        self.show_cursor = not self.show_cursor
        self.dirty_surface = True

    def do_on_click_down(self, button):
        if button != 1:
            return
        self.get_focus()

    def do_on_enter(self):
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_IBEAM)

    def do_on_exit(self):
        pygame.mouse.set_cursor(bf.const.DEFAULT_CURSOR)

    def do_on_get_focus(self):
        self.old_key_repeat = pygame.key.get_repeat()
        self.cursor_timer.resume()
        pygame.key.set_repeat(200, 50)

    def do_on_lose_focus(self):
        self.cursor_timer.pause()
        pygame.key.set_repeat(*self.old_key_repeat)

    def set_cursor_position(self, position: int) -> Self:
        if position < 0:
            position = 0
        elif position > len(self.get_text()):
            position = len(self.get_text())
        self.cursor_position = position
        self.show_cursor = True
        self.dirty_surface = True
        return self

    def do_handle_event(self, event) -> bool:
        if not self.is_focused:
            return False

        text = self.get_text()
        cursor_position = self.cursor_position

        if event.type == pygame.TEXTINPUT:
            self.set_text(text[:cursor_position] + event.text + text[cursor_position:])
            self.set_cursor_position(cursor_position + 1)
            return True

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.lose_focus()
        
            if event.key == pygame.K_BACKSPACE:
                if cursor_position > 0:
                    self.set_text(text[:cursor_position - 1] + text[cursor_position:])
                    self.set_cursor_position(cursor_position - 1)
                return True

            if event.key == pygame.K_RIGHT:
                self.set_cursor_position(cursor_position + 1)
                return True

            if event.key == pygame.K_LEFT:
                self.set_cursor_position(cursor_position - 1)
                return True

            if event.key in [pygame.K_UP, pygame.K_DOWN]:
                return False

        return False


    def _paint_cursor(self) -> None:
        if not self.font_object or not self.show_cursor:
            return
        partial_text_size = self.font_object.size(
            self.get_text()[: self.cursor_position]
        )
        
        cursor_rect = pygame.Rect(0, 0,1, self.font_object.point_size )
        if self.cursor_position != 0:  # align left properly
            cursor_rect.midleft = self.text_rect.move(partial_text_size[0], 0).midleft
        else:
            cursor_rect.midright = self.text_rect.midleft

        pygame.draw.rect(self.surface, self.text_color, cursor_rect)

    def paint(self) -> None:
        super().paint()
        if self.is_focused:
            self._paint_cursor()

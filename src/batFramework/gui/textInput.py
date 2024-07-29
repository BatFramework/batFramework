import batFramework as bf
from typing import Self, Callable
from .label import Label
from .interactiveWidget import InteractiveWidget
import pygame

def find_next_word(s: str, start_index: int) -> int:
    length = len(s)
    # Ensure the starting index is within the bounds of the string
    if start_index < 0 or start_index >= length:
        raise ValueError("Starting index is out of bounds")
    index = start_index
    # If the start_index is at a space, skip leading spaces
    if s[index] in [' ','\n']:
        while index < length and s[index]  in [' ','\n']:
            index += 1
        # If we've reached the end of the string
        if index >= length:
            return -1
    else:
        # If the start_index is within a word, move to the end of that word
        while index < length and s[index] not in [' ','\n']:
            index += 1
        if index == length:
            return index    
    # Return the index of the start of the next word or -1 if no more words are found
    return index if index < length else -1

def find_prev_word(s: str, start_index: int) -> int:
    if start_index <= 0 : return 0
    length = len(s)
    
    # Ensure the starting index is within the bounds of the string
    if start_index < 0 or start_index >= length:
        raise ValueError("Starting index is out of bounds")
    
    index = start_index
    
    # If the start_index is at a space, skip trailing spaces
    if s[index] in [' ', '\n']:
        while index > 0 and s[index-1] in [' ', '\n']:
            index -= 1
        # If we've reached the beginning of the string
        if index <= 0:
            return 0 if s[0] not in [' ', '\n'] else -1
    else:
        # If the start_index is within a word, move to the start of that word
        while index > 0 and s[index-1] not in [' ', '\n']:
            index -= 1
        if index == 0 and s[index] not in [' ', '\n']:
            return 0
    
    # Return the index of the start of the previous word or -1 if no more words are found
    return index if index > 0 or (index == 0 and s[0] not in [' ', '\n']) else -1


class TextInput(Label, InteractiveWidget):
    def __init__(self) -> None:
        self.cursor_position = (0, 0)
        self.old_key_repeat = (0, 0)
        self.cursor_timer = bf.Timer(0.3, self._cursor_toggle, loop=True).start()
        self.cursor_timer.pause()
        self.show_cursor = False
        self.on_modify: Callable[[str], str] = None
        self.set_focusable(True)
        self.set_outline_color("black")
        super().__init__("")
        self.alignment = bf.alignment.TOPLEFT

    def set_modify_callback(self, callback: Callable[[str], str]) -> Self:
        self.on_modify = callback
        return self

    def __str__(self) -> str:
        return f"TextInput({repr(self.text)})"

    def _cursor_toggle(self, value: bool | None = None):
        if value is None:
            value = not self.show_cursor
        self.show_cursor = value
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
        self.cursor_timer.resume()
        self._cursor_toggle(True)
        self.old_key_repeat = pygame.key.get_repeat()
        pygame.key.set_repeat(200, 50)

    def do_on_lose_focus(self):
        self.cursor_timer.pause()
        self._cursor_toggle(False)
        pygame.key.set_repeat(*self.old_key_repeat)

    def get_line(self, line: int) -> str | None:
        if line < 0:
            return None
        lines = self.text.split('\n')
        if line >= len(lines):
            return None
        return lines[line]

    def set_cursor_position(self, position: tuple[int, int]) -> Self:
        x, y = position

        lines = self.text.split('\n')
        y = max(0, min(y, len(lines) - 1))
        line_length = len(lines[y])
        x = max(0, min(x, line_length))

        self.cursor_position = (x, y)
        self.show_cursor = True
        self.dirty_shape = True
        return self

    def cursor_to_absolute(self, position: tuple[int, int]) -> int:
        x, y = position

        y = max(0, min(y, len(self.text.split('\n')) - 1))
        lines = self.text.split('\n')
        x = max(0, min(x, len(lines[y])))

        absolute_position = sum(len(line) + 1 for line in lines[:y]) + x
        return absolute_position

    def absolute_to_cursor(self, absolute: int) -> tuple[int, int]:
        text = self.text
        lines = text.split('\n')
        current_pos = 0

        for line_no, line in enumerate(lines):
            if absolute <= current_pos + len(line):
                return (absolute - current_pos, line_no)
            current_pos += len(line) + 1

        return (len(lines[-1]), len(lines) - 1)

    def do_handle_event(self, event):
        if not self.is_focused:
            return

        if event.type not in [pygame.TEXTINPUT, pygame.KEYDOWN]:
            return

        text = self.get_text()
        current = self.cursor_to_absolute(self.cursor_position)
        if event.type == pygame.TEXTINPUT:
            self.set_text(text[:current] + event.text + text[current:])
            self.set_cursor_position(self.absolute_to_cursor(current + len(event.text)))
        elif event.type == pygame.KEYDOWN:
            pressed = pygame.key.get_pressed()
            if event.key == pygame.K_ESCAPE:
                self.lose_focus()
            elif event.key == pygame.K_BACKSPACE:
                if current > 0:
                    self.set_text(text[:current - 1] + text[current:])
                    self.set_cursor_position(self.absolute_to_cursor(current - 1))
            elif event.key == pygame.K_DELETE:
                if current < len(text):
                    self.set_text(text[:current] + text[current + 1:])
            elif event.key == pygame.K_RIGHT:
                if self.cursor_to_absolute(self.cursor_position)>=len(self.text):
                    return
                if self.cursor_position[0] == len(self.get_line(self.cursor_position[1])):
                    self.set_cursor_position((0, self.cursor_position[1] + 1))
                else:
                    if pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]:
                        index = find_next_word(self.text,current)
                        if index ==-1 : index = current+1
                        self.set_cursor_position(self.absolute_to_cursor(index))
                    else:
                        self.set_cursor_position(self.absolute_to_cursor(current + 1))
            elif event.key == pygame.K_LEFT:


                if self.cursor_position[0] == 0 and self.cursor_position[1] > 0:
                    self.set_cursor_position((len(self.get_line(self.cursor_position[1] - 1)), self.cursor_position[1] - 1))
                else:
                    if pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]:
                        index = find_prev_word(self.text,current-1)
                        if index ==-1 : index = current-1
                        self.set_cursor_position(self.absolute_to_cursor(index))
                    else:
                        self.set_cursor_position(self.absolute_to_cursor(current - 1))
            elif event.key == pygame.K_UP:
                x, y = self.cursor_position
                self.set_cursor_position((x, y - 1))
            elif event.key == pygame.K_DOWN:
                x, y = self.cursor_position
                self.set_cursor_position((x, y + 1))
            elif event.key == pygame.K_RETURN:
                self.set_text(text[:current] + '\n' + text[current:])
                self.set_cursor_position(self.absolute_to_cursor(current + 1))
            else:
                return
        else:
            return

        event.consumed = True

    def set_text(self, text: str) -> Self:
        if self.on_modify:
            text = self.on_modify(text)
        return super().set_text(text)

    def _paint_cursor(self) -> None:
        if not self.font_object or not self.show_cursor:
            return

        lines = self.text.split('\n')
        line_x, line_y = self.cursor_position

        cursor_y = self.padding[1] 
        cursor_y += line_y * self.font_object.get_linesize()
        cursor_x = self.padding[0]
        cursor_x += self.font_object.size(lines[line_y][:line_x])[0] if line_x > 0 else 0

        cursor_rect = pygame.Rect(cursor_x, cursor_y, 2, self.font_object.get_height())
        pygame.draw.rect(self.surface, self.text_color, cursor_rect)

    def paint(self) -> None:
        super().paint()
        self._paint_cursor()

    # def set_alignment(self, alignment: bf.alignment) -> Self:
    #     return self

    # def align_text(
    #     self, text_rect: pygame.FRect, area: pygame.FRect, alignment: bf.alignment
    # ):
    #     if alignment == bf.alignment.LEFT:
    #         alignment = bf.alignment.MIDLEFT
    #     elif alignment == bf.alignment.MIDRIGHT:
    #         alignment = bf.alignment.MIDRIGHT
    #     pos = area.__getattribute__(alignment.value)
    #     text_rect.__setattr__(alignment.value, pos)
    #     return

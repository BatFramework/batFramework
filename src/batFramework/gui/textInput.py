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
        self.cursor_timer = bf.Timer(0.2, self._cursor_toggle, loop=True).start()
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

    def get_debug_outlines(self):
        if self.visible:
            offset = self._get_outline_offset() if self.show_text_outline else (0,0)
            yield (self.text_rect.move(self.rect.x - offset[0] - self.scroll.x,self.rect.y - offset[1] - self.scroll.y), "purple")
        yield from super().get_debug_outlines()
        yield (self.get_cursor_rect().move(-self.scroll+self.rect.topleft),"green")


    def set_cursor_position(self, position: tuple[int, int]) -> Self:
        x, y = position

        lines = self.text.split('\n')
        y = max(0, min(y, len(lines) - 1))
        line_length = len(lines[y])
        x = max(0, min(x, line_length))
        self.show_cursor = True
        self.cursor_position = (x,y)
        self.dirty_surface = True
        offset = self._get_outline_offset() if self.show_text_outline else (0,0)
        padded = self.get_padded_rect().move(-self.rect.x + offset[0], -self.rect.y + offset[1])
        self.align_text(self.text_rect,padded,self.alignment)
        return self

    def get_cursor_rect(self)->pygame.FRect:
        if not self.font_object:
            return pygame.FRect(0,0,0,0)

        lines = self.text.split('\n')
        line_x, line_y = self.cursor_position

        height = self.font_object.get_linesize()

        cursor_y = self.get_padded_rect().__getattribute__(self.alignment.value)[1] - self.rect.top
        cursor_y += line_y * height
        cursor_x = self.text_rect.x
        cursor_x += self.font_object.size(lines[line_y][:line_x])[0] if line_x > 0 else 0
        cursor_rect = pygame.Rect(cursor_x, cursor_y, 1, height)
        return cursor_rect

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
        if not self.is_focused or event.type not in [pygame.TEXTINPUT, pygame.KEYDOWN]:
            return

        text = self.get_text()
        current_pos = self.cursor_to_absolute(self.cursor_position)
        pressed = pygame.key.get_pressed()

        if event.type == pygame.TEXTINPUT:
            # Insert text at the current cursor position
            self.set_text(f"{text[:current_pos]}{event.text}{text[current_pos:]}")
            self.set_cursor_position(self.absolute_to_cursor(current_pos + len(event.text)))

        elif event.type == pygame.KEYDOWN:
            match event.key:
                case pygame.K_ESCAPE:
                    self.lose_focus()

                case pygame.K_BACKSPACE if current_pos > 0:
                    # Remove the character before the cursor
                    self.set_text(f"{text[:current_pos - 1]}{text[current_pos:]}")
                    self.set_cursor_position(self.absolute_to_cursor(current_pos - 1))

                case pygame.K_DELETE if current_pos < len(text):
                    # Remove the character at the cursor
                    self.set_text(f"{text[:current_pos]}{text[current_pos + 1:]}")

                case pygame.K_RIGHT:
                    if current_pos < len(text):
                        self.handle_cursor_movement(pressed, current_pos, direction="right")

                case pygame.K_LEFT:
                    if current_pos > 0:
                        self.handle_cursor_movement(pressed, current_pos, direction="left")

                case pygame.K_UP:
                    # Move cursor up one line
                    self.set_cursor_position((self.cursor_position[0], self.cursor_position[1] - 1))

                case pygame.K_DOWN:
                    # Move cursor down one line
                    self.set_cursor_position((self.cursor_position[0], self.cursor_position[1] + 1))

                case pygame.K_RETURN:
                    # Insert a newline at the current cursor position
                    self.set_text(f"{text[:current_pos]}\n{text[current_pos:]}")
                    self.set_cursor_position(self.absolute_to_cursor(current_pos + 1))
                case _ :
                    return

        event.consumed = True

    def handle_cursor_movement(self, pressed, current_pos, direction):
        if direction == "right":
            if pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]:
                next_word_pos = find_next_word(self.text, current_pos)
                self.set_cursor_position(self.absolute_to_cursor(next_word_pos if next_word_pos != -1 else current_pos + 1))
            else:
                self.set_cursor_position(self.absolute_to_cursor(current_pos + 1))
        elif direction == "left":
            if pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]:
                prev_word_pos = find_prev_word(self.text, current_pos - 1)
                self.set_cursor_position(self.absolute_to_cursor(prev_word_pos if prev_word_pos != -1 else current_pos - 1))
            else:
                self.set_cursor_position(self.absolute_to_cursor(current_pos - 1))


    def set_text(self, text: str) -> Self:
        if self.on_modify:
            text = self.on_modify(text)
        return super().set_text(text)

    def _paint_cursor(self) -> None:
        if not self.font_object or not self.show_cursor:
            return
        cursor_rect = self.get_cursor_rect()
        cursor_rect.move_ip(-self.scroll)
        
        pygame.draw.rect(self.surface, bf.color.CLOUD, cursor_rect.inflate(2,2))
        pygame.draw.rect(self.surface, self.text_color, cursor_rect)

    def paint(self) -> None:
        super().paint()
        self._paint_cursor()

    def align_text(
        self, text_rect: pygame.FRect, area: pygame.FRect, alignment: bf.alignment
    ):
        cursor_rect = self.get_cursor_rect()
        
        if alignment == bf.alignment.LEFT:
            alignment = bf.alignment.MIDLEFT
        elif alignment == bf.alignment.MIDRIGHT:
            alignment = bf.alignment.MIDRIGHT
        pos = area.__getattribute__(alignment.value)
        text_rect.__setattr__(alignment.value, pos)

        
        if cursor_rect.right > area.right+self.scroll.x:
            self.scroll.x=cursor_rect.right - area.right - cursor_rect.w*2 
        elif cursor_rect.x < self.scroll.x+area.left:
            self.scroll.x= cursor_rect.left - area.left
        self.scroll.x = max(self.scroll.x,0)

        if cursor_rect.bottom > area.bottom + self.scroll.y:
            self.scroll.y = cursor_rect.bottom - area.bottom
        elif cursor_rect.y < self.scroll.y + area.top:
            self.scroll.y = cursor_rect.top - area.top
        self.scroll.y = max(self.scroll.y, 0)

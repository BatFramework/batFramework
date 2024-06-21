import batFramework as bf
from typing import Self,Callable
from .label import Label
from .interactiveWidget import InteractiveWidget
import pygame


class TextInput(Label, InteractiveWidget):
    def __init__(self) -> None:
        self.cursor_position = 0
        self.old_key_repeat: tuple = (0, 0)
        self.cursor_timer = bf.Timer(0.3, self._cursor_toggle, loop=True).start()
        self.cursor_timer.pause()
        self.show_cursor: bool = False
        self.on_modify :Callable[[str],str] = None 
        self.set_focusable(True)
        self.set_outline_color("black")
        super().__init__("")

    def set_modify_callback(self,callback : Callable[[str],str])->Self:
        self.on_modify = callback
        return self

    def to_string_id(self) -> str:
        return f"TextInput({self.text})"

    def _cursor_toggle(self,value:bool = None):
        if value is None : value = not self.show_cursor
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
        self.old_key_repeat = pygame.key.get_repeat()
        self.cursor_timer.resume()
        self._cursor_toggle(True)
        pygame.key.set_repeat(200, 50)

    def do_on_lose_focus(self):
        self.cursor_timer.pause()
        self._cursor_toggle(False)
        pygame.key.set_repeat(*self.old_key_repeat)

    def set_cursor_position(self, position: int) -> Self:
        if position < 0:
            position = 0
        elif position > len(self.get_text()):
            position = len(self.get_text())
        self.cursor_position = position
        self.show_cursor = True
        self.dirty_surface = True
        if self.text_rect.w > self.get_padded_width():
            self.dirty_shape = True
        return self

    def do_handle_event(self, event):
        if not self.is_focused:
            return
        text = self.get_text()
        cursor_position = self.cursor_position

        if event.type == pygame.TEXTINPUT:
            self.set_text(text[:cursor_position] + event.text + text[cursor_position:])
            self.set_cursor_position(cursor_position + 1)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.lose_focus()
        
            elif event.key == pygame.K_BACKSPACE:
                if cursor_position > 0:
                    self.set_text(text[:cursor_position - 1] + text[cursor_position:])
                    self.set_cursor_position(cursor_position - 1)

            elif event.key == pygame.K_RIGHT:
                self.set_cursor_position(cursor_position + 1)

            elif event.key == pygame.K_LEFT:
                self.set_cursor_position(cursor_position - 1)

            else:
                return
        else : 
            return

        event.consumed = True
        
    def set_text(self, text: str) -> Self:
        if self.on_modify : text = self.on_modify(text)
        return super().set_text(text)

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
        self._paint_cursor()


    def align_text(self,text_rect:pygame.FRect,area:pygame.FRect,alignment: bf.alignment):
        if alignment == bf.alignment.LEFT : alignment = bf.alignment.MIDLEFT
        elif alignment == bf.alignment.MIDRIGHT : alignment = bf.alignment.MIDRIGHT

        pos = area.__getattribute__(alignment.value)
        text_rect.__setattr__(alignment.value,pos)
        w = self.font_object.size(
            self.get_text()[: self.cursor_position]
        )[0]
        if self.text_rect.x + w > area.right:
            self.text_rect.right = area.right
        elif self.text_rect.x + w < area.left:
            self.text_rect.left = area.left - w
        
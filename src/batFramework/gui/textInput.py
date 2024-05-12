import batFramework as bf
from typing import Self
from .label import Label
from .interactiveWidget import InteractiveWidget
import pygame

class TextInput(Label,InteractiveWidget):
    def __init__(self)->None:
        self.cursor_position = 0
        super().__init__("A")
        self.set_text("")
        self.set_focusable(True)
        self.set_outline_color("black")
        self.old_key_repeat :tuple= (0,0)
        self.cursor_timer = bf.Timer(0.3,self._cursor_toggle,loop=True).start()
        self.cursor_timer.pause()
        self.show_cursor :bool = True

    def to_string_id(self) -> str:
        return f"TextInput({self.text})"

    def _cursor_toggle(self):
        self.show_cursor = not self.show_cursor
        self.build()

    def do_on_click_down(self,button):
        if button != 1:return
        self.get_focus()
    def do_on_enter(self):
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_IBEAM)

    def do_on_exit(self):
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    def do_on_get_focus(self):
        self.set_outline_width(2)
        self.old_key_repeat = pygame.key.get_repeat()
        self.cursor_timer.resume()
        pygame.key.set_repeat(200,50)
    def do_on_lose_focus(self):
        self.set_outline_width(0)
        self.cursor_timer.pause()
        pygame.key.set_repeat(*self.old_key_repeat)

    def set_cursor_position(self,position:int)->Self:
        if position < 0 : position = 0
        elif position > len(self.get_text()): position = len(self.get_text())
        self.cursor_position = position
        self.show_cursor = True
        self.build()
        return self

    def do_handle_event(self,event)->bool:
        text = self.get_text()
        if not self.is_focused : return False
        if event.type == pygame.TEXTINPUT:
            self.set_text(text[:self.cursor_position]+event.text+text[self.cursor_position:])
            self.set_cursor_position(self.cursor_position+1)
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
            if self.cursor_position != 0 : 
                self.set_text(text[:self.cursor_position-1]+text[self.cursor_position:])
                self.set_cursor_position(self.cursor_position-1)
            return True

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
            self.set_cursor_position(self.cursor_position+1)
            return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT:
            self.set_cursor_position(self.cursor_position-1)
            return True

        if event.type == pygame.KEYDOWN and event.key in [pygame.K_UP,pygame.K_DOWN]:
            return True
        
        return False

    def _build_cursor(self)->None:
        if not self.font_object : return
        if not self.show_cursor : return
        partial_text_size = self.font_object.size(self.get_text()[:self.cursor_position])
        cursor_rect = pygame.Rect(0,0,2,partial_text_size[1]+2)
        if self.cursor_position != 0:#align left properly
            cursor_rect.midleft = self.text_rect.move(partial_text_size[0],0).midleft
        else:
            cursor_rect.midright = self.text_rect.midleft

        pygame.draw.rect(self.surface, self.text_color, cursor_rect)

    def build(self)->None:
        super().build()
        if self.is_focused : self._build_cursor()

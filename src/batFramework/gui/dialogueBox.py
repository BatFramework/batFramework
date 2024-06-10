from .label import Label
import batFramework as bf
from typing import Self


class DialogueBox(Label):
    def __init__(self) -> None:
        self.cursor_position: float = 0.0
        self.text_speed: float = 20.0
        self.message_queue: list[str] = []
        self.is_over: bool = True
        self.is_paused: bool = False
        self.set_autoresize(False)
        self.set_alignment(bf.alignment.LEFT)
        super().__init__("")

    def pause(self)->Self:
        self.is_paused = True
        return self
    
    def resume(self)->Self:
        self.is_paused = False
        return self

    def set_text_speed(self, speed: float) -> Self:
        self.text_speed = speed
        return self

    def cut_text_to_width(self, text: str) -> list[str]:
        w = self.get_padded_width()
        if text == "" or not self.font_object or  w < self.font_object.point_size:
            return [text]
        left = 0
        for index in range(len(text)):
            width = self.font_object.size(text[left:index])[0]
            
            if width > w:
                cut_point_start = index - 1
                cut_point_end = index - 1
                last_space = text.rfind(' ', 0, cut_point_start)
                last_nline = text.rfind('\n', 0, cut_point_start)

                if last_space != -1 or last_nline!= -1:  # space was found !:
                    cut_point_start = max(last_space,last_nline)
                    cut_point_end = cut_point_start + 1
                res = [text[:cut_point_start].strip()]
                res.extend(self.cut_text_to_width(text[cut_point_end:].strip()))
                return res
            elif text[index] == '\n':
                left = index
        return [text]

    def paint(self)->None:
        if self.font_object and self.message_queue :
            message = self.message_queue.pop(0)
            message = "\n".join(self.cut_text_to_width(message))
            self.message_queue.insert(0,message)
        super().paint()
 
    def say(self, message: str) ->Self:
        self.message_queue.append(message)
        self.is_over = False
        return self
    
    def is_queue_empty(self) -> bool:
        return not self.message_queue

    def is_current_message_over(self) -> bool:
        return self.is_over

    def clear_queue(self) -> Self:
        self.message_queue.clear()
        self.next_message()
        return self

    def next_message(self) -> Self:
        if self.message_queue:
            self.message_queue.pop(0)
        self.cursor_position = 0
        self.set_text("")
        return self

    def skip_current_message(self)->Self:
        self.cursor_position = len(self.message_queue[0])
        self.dirty_shape = True

    def do_update(self, dt):
        if not self.message_queue or self.is_paused:
            return
        if not self.is_over and self.cursor_position == len(self.message_queue[0]):
            self.is_over = True
            return
        self.cursor_position = min(
            self.cursor_position + self.text_speed * dt, len(self.message_queue[0])
        )
        self.set_text(self.message_queue[0][: int(self.cursor_position)])

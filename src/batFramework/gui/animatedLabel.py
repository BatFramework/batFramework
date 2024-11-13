from .label import Label
import batFramework as bf
from typing import Self


class AnimatedLabel(Label):
    def __init__(self,text="") -> None:
        self.cursor_position: float = 0.0
        self.text_speed: float = 20.0
        self.is_over: bool = True
        self.is_paused: bool = False
        self.original_text = ""
        self.set_autoresize(False)
        self.set_alignment(bf.alignment.LEFT)
        super().__init__("")
        self.set_text(text)

    def __str__(self) -> str:
        return "AnimatedLabel"

    def pause(self) -> Self:
        self.is_paused = True
        return self

    def resume(self) -> Self:
        self.is_paused = False
        return self

    def set_text_speed(self, speed: float) -> Self:
        self.text_speed = speed
        return self

    def cut_text_to_width(self, text: str) -> list[str]:
        w = self.get_padded_width()
        if text == "" or not self.font_object or w < self.font_object.point_size:
            return [text]
        left = 0
        for index in range(len(text)):
            width = self.font_object.size(text[left:index])[0]

            if width > w:
                cut_point_start = index - 1
                cut_point_end = index - 1
                last_space = text.rfind(" ", 0, cut_point_start)
                last_nline = text.rfind("\n", 0, cut_point_start)

                if last_space != -1 or last_nline != -1:  # space was found !:
                    cut_point_start = max(last_space, last_nline)
                    cut_point_end = cut_point_start + 1
                res = [text[:cut_point_start].strip()]
                res.extend(self.cut_text_to_width(text[cut_point_end:].strip()))
                return res
            elif text[index] == "\n":
                left = index
        return [text]


    def _set_text_internal(self,text:str)->Self:
        super().set_text(text)
        return self

    def set_text(self,text:str)->Self:
        self.original_text = text
        self.is_over = False
        self.cursor_position = 0

    def set_size(self, size):
        super().set_size(size)
        self._set_text_internal('\n'.join(self.cut_text_to_width(self.original_text[: int(self.cursor_position)])))

    def do_update(self, dt):
        if self.is_over:
            return
        if not self.is_over and self.cursor_position == len(self.original_text):
            self.is_over = True
            return
        self.cursor_position = min(
            self.cursor_position + self.text_speed * dt, len(self.original_text)
        )
        # self.set_text(self.original_text[: int(self.cursor_position)])
        self._set_text_internal('\n'.join(self.cut_text_to_width(self.original_text[: int(self.cursor_position)])))

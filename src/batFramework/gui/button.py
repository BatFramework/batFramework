from .label import Label
import batFramework as bf
from typing import Self, Callable, Any
from .clickableWidget import ClickableWidget


class Button(Label, ClickableWidget):
    def __init__(self, text: str = "", callback: Callable[[], Any] = None) -> None:
        super().__init__(text=text)
        self.set_callback(callback)
        self.set_debug_color("brown")


    def __str__(self) -> str:
        return f"Button('{repr(self.text)}')"

    def get_min_required_size(self):
        res = Label.get_min_required_size(self)
        res =  res[0], res[1] + self.unpressed_relief
        return res
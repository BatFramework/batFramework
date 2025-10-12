from .label import Label
import batFramework as bf
from typing import Self, Callable,Any
from .clickableWidget import ClickableWidget


class Button(Label, ClickableWidget):
    def __init__(self, text: str = "", callback: Callable[[],Any] = None) -> None:
        super().__init__(text=text)
        self.set_callback(callback)

    def __str__(self) -> str:
        return f"Button('{self.text_widget.text}')"

    def get_min_required_size(self):
        res = super().get_min_required_size()
        res = res[0],res[1]+self.unpressed_relief
        return res
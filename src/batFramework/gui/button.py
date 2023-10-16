from .label import Label

from types import FunctionType

class Button(Label):
    def __init__(self, text: str, callback : FunctionType =None) -> None:
        self.callback = callback
        
        super().__init__(text)
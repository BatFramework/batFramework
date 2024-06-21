import batFramework as bf
from typing import Self,Any,Callable
from .toggle import Toggle

class RadioVariable:...

class RadioButton(Toggle):
    def __init__(self, text: str, radio_value:Any = None) -> None:
        super().__init__(text,None, False)
        self.radio_value : Any = radio_value if radio_value is not None else text if text else None
        self.radio_variable : RadioVariable = None

    def set_radio_value(self,value:Any)->Self:
        self.radio_value = value
        self.update_radio()
        return self
    
    def set_text(self, text: str) -> Self:
        flag = False
        if self.value == self.text or self.value is None: flag = True
        super().set_text(text)
        if flag:
            self.set_radio_value(self.text)
        return self

    def click(self) -> None:
        if self.radio_variable is None: return
        self.radio_variable.set_value(self.radio_value)

class RadioVariable:
    def __init__(self)->None:
        self.buttons : list[RadioButton] = []
        self.value = None
        self.modify_callback : Callable[[Any],] = None

    def link(self,*buttons:RadioButton)->Self:
        if not buttons : return self
        for b in buttons : 
            b.radio_variable = self
        self.buttons.extend(buttons)
        
        if self.value is None:
            self.set_value(buttons[0].radio_value)
        else:
            self.update_buttons() 
        return self

    def unlink(self,*buttons)->Self:
        for b in self.buttons:
            if b in buttons:
                b.radio_variable = None
        self.buttons = [b for b in self.buttons if b not in buttons]
        return self

    def set_value(self,value:Any):
        if value == self.value: return
        self.value = value
        if self.modify_callback :self.modify_callback(value)
        self.update_buttons() 

    def update_buttons(self):
        _ = [b.set_value(b.radio_value == self.value,False) for b in self.buttons]
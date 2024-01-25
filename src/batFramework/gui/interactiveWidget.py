from .widget import Widget
from typing import Self

class InteractiveWidget(Widget):
    def __init__(self, *args, **kwargs)->None:
        self.focusable = True
        self.is_focused: bool = False
        self.is_hovered: bool = False
        self.is_clicked_down:bool = False
        super().__init__(convert_alpha=True)

    def set_focusable(self,value:bool)->Self:
        self.focusable = value
        return self

    def get_focus(self) -> bool:
        if self.focusable and (r:=self.get_root()) is not None:
            r.focus_on(self)
            return True
        return False

    def lose_focus(self) -> bool:
        if self.is_focused  and (r:=self.get_root()) is not None:
            r.focus_on(None)
            return True
        return False

        
    def on_get_focus(self) -> None:
        self.is_focused = True
        self.do_on_get_focus()


    def on_lose_focus(self) -> None:
        self.is_focused = False
        self.do_on_lose_focus()


    def do_on_get_focus(self)->None:
        pass
        
    def do_on_lose_focus(self)->None:
        pass


    def on_click_down(self,button:int)->None:
        self.do_on_click_down(button)

    def on_click_up(self,button:int)->None:
        self.do_on_click_up(button)

    def do_on_click_down(self,button:int)->None:    
        pass

    def do_on_click_up(self,button:int)->None:
        pass

    def on_enter(self)->None:
        self.is_hovered = True
        self.do_on_enter()

    def on_exit(self)->None:
        self.is_hovered = False
        self.do_on_exit()


    def do_on_enter(self)->None:
        pass

    def do_on_exit(self)->None:
        pass



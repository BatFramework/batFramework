from .widget import Widget

class InteractiveWidget(Widget):
    def __init__(self, *args, **kwargs)->None:
        self.focusable = True
        self.is_focused: bool = False
        self.is_hovered: bool = False
        self.is_clicked_down:bool = False
        super().__init__(convert_alpha=True)

    def get_focus(self) -> bool:
        if self.parent is None and  self.focusable and (r:=self.get_root()) is not None:
            r.focus_on(self)
            return True
        return False
    def on_get_focus(self) -> None:
        self.is_focused = True

    def on_lose_focus(self) -> None:
        self.is_focused = False

    def lose_focus(self) -> bool:
        if self.is_focused and self.parent is not None and (r:=self.get_root()) is not None:
            r.focus_on(None)
            return True
        return False

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

    def do_on_enter(self)->None:
        pass

    def on_exit(self)->None:
        self.is_hovered = False
        self.do_on_exit()

    def do_on_exit(self)->None:
        pass



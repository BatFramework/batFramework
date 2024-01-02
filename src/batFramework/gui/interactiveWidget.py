from .widget import Widget


class InteractiveWidget(Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(convert_alpha=True)
        self.focusable = True
        self.is_focused: bool = False

    def get_focus(self) -> bool:
        if self.parent is None or not self.focusable:
            return False
        self.get_root().focus_on(self)

    def on_get_focus(self) -> None:
        self.is_focused = True

    def on_lose_focus(self) -> None:
        self.is_focused = False

    def lose_focus(self) -> bool:
        if self.is_focused and self.parent is not None:
            self.get_root().focus_on(None)

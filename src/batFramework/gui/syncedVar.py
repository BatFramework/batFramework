from typing import TypeVar, Generic, Callable, Any
from .widget import Widget

T = TypeVar('T')

class SyncedVar(Generic[T]):
    def __init__(self, value: T = None):
        self._value: T = value
        self.modify_callback: Callable[[T], Any] | None = None
        self._bound_widgets: set[tuple[Widget, Callable[[T], Any]]] = set()

    def set_modify_callback(self, callback: Callable[[T], Any]) -> "SyncedVar[T]":
        self.modify_callback = callback
        return self

    def bind_widget(self, widget: Widget, update_callback: Callable[[T], Any]) -> "SyncedVar[T]":
        self._bound_widgets.add((widget, update_callback))
        return self

    def unbind_widget(self, widget: Widget) -> "SyncedVar[T]":
        self._bound_widgets = {(w, cb) for w, cb in self._bound_widgets if w != widget}
        return self

    @property
    def value(self) -> T:
        return self._value

    @value.setter
    def value(self, new_value: T):
        if self._value != new_value:
            self._value = new_value
            self.update_widgets()
        if self.modify_callback is not None:
            self.modify_callback(new_value)

    def update_widgets(self):
        for _, update_callback in self._bound_widgets:
            update_callback(self._value)

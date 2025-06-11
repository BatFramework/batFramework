from .widget import Widget
from typing import Callable, Any, Self

class SyncedVar:
    def __init__(self, value=None):
        self._value: Any = value
        self.modify_callback: Callable[[Any], Any] | None = None
        self._bound_widgets: set[tuple[Widget, Callable[[Any], Any]]] = set()

    def set_modify_callback(self, callback : Callable[[Any], Any]) -> Self:
        self.modify_callback = callback
        return self

    def bind_widget(self, widget: Widget, update_callback: Callable[[Any], Any]) -> Self:
        """
        Binds a widget to the SyncedVar. The widget must provide an update_callback
        function that will be called whenever the value changes.
        """
        self._bound_widgets.add((widget, update_callback))
        self._update_widgets()
        return self

    def unbind_widget(self, widget: Widget)->Self:
        """
        Unbinds a widget from the SyncedVar.
        """
        self._bound_widgets = {
            (w, cb) for w, cb in self._bound_widgets if w != widget
        }
        return self

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if self._value != new_value:
            self._value = new_value
            self._update_widgets()
        if self.modify_callback is not None:
            self.modify_callback(new_value)

    def _update_widgets(self):
        """
        Calls the update callback for all bound widgets.
        """
        for _, update_callback in self._bound_widgets:
            update_callback(self._value)
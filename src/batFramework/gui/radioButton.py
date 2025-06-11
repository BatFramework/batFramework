import batFramework as bf
from typing import Self, Any, Callable
from .toggle import Toggle
from .syncedVar import SyncedVar


class RadioButton(Toggle):
    def __init__(self, text: str = "", radio_value: Any = None, synced_var: SyncedVar = None) -> None:
        super().__init__(text, None, False)
        self.radio_value: Any = radio_value if radio_value is not None else text if text else None
        self.synced_var : SyncedVar = None
        if synced_var:
            self.link(synced_var)

    def link(self,synced_var:SyncedVar)->Self:
        self.synced_var = synced_var
        synced_var.bind_widget(self,self._update_state)
        return self

    def __str__(self) -> str:
        return f"RadioButton({self.radio_value}|{'Active' if self.value else 'Inactive'})"

    def set_radio_value(self, value: Any) -> Self:
        self.radio_value = value
        return self

    def set_value(self, value : bool, do_callback=False):
        super().set_value(value, do_callback)
        if value : self.synced_var.value = self.radio_value

    def _update_state(self, synced_value: Any) -> None:
        """
        Updates the state of the RadioButton based on the synced variable's value.
        """
        self.set_value(self.radio_value == synced_value, False)

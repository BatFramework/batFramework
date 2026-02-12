import batFramework as bf
from typing import Self, Any, Callable
from .toggle import Toggle
from .syncedVar import SyncedVar


# TODO : RadioButton with no synced var ? click crashes

class RadioButton(Toggle):
    def __init__(self, text: str, synced_var: SyncedVar, radio_value: Any = None) -> None:
        super().__init__(text, None, False)
        self.radio_value: Any = radio_value if radio_value is not None else text if text else None
        self.synced_var : SyncedVar = synced_var
        self.synced_var.bind(self,self._update_state)
        self.set_value(synced_var.value, False)

    def __str__(self) -> str:
        return f"RadioButton({self.radio_value}|{'Active' if self.value else 'Inactive'})"

    def set_radio_value(self, value: Any) -> Self:
        self.radio_value = value
        return self

    def click(self):
        if self.value : return
        self.set_value(True, True)

    def set_value(self, value : bool, do_callback=False):
        if self.value == value:
            return self  # No change
        self.value = value
        self.indicator.set_value(value)
        self.dirty_surface = True

        # Update SyncedVar only if different (avoid recursion)
        if value and self.synced_var.value != self.radio_value:
            self.synced_var.value = self.radio_value

        if do_callback and self.callback:
            self.callback(self.value)
        return self
        # if value : self.synced_var.value = self.radio_value

    def _update_state(self, synced_value: Any) -> None:
        """
        Updates the state of the RadioButton based on the synced variable's value.
        """
        self.set_value(self.radio_value == synced_value, False)

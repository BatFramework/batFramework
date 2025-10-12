from typing import TypeVar, Generic, Callable, Any, Self
from .widget import Widget
from ..entity import Entity

T = TypeVar('T')

class SyncedVar(Generic[T]):
    def __init__(self, value: T = None):
        self._value: T = value
        self.modify_callback: Callable[[T], Any] | None = None
        self._bound_entities: set[tuple[Entity, Callable[[T], Any]]] = set()

    def set_modify_callback(self, callback: Callable[[T], Any]) -> "SyncedVar[T]":
        self.modify_callback = callback
        return self

    def bind(self, entity, update_callback: Callable[[T], Any]) -> "SyncedVar[T]":
        self._bound_entities.add((entity, update_callback))
        return self

    def unbind(self, entity: Entity) -> "SyncedVar[T]":
        self._bound_entities = {(e, cb) for e, cb in self._bound_entities if e != entity}
        return self

    @property
    def value(self) -> T:
        return self._value

    def set_value(self,value:T)->Self:
        self.value = value
        return self

    @value.setter
    def value(self, new_value: T):
        if self._value != new_value:
            self._value = new_value
            self.update_bound_entities()
            if self.modify_callback is not None:
                self.modify_callback(new_value)

    def update_bound_entities(self):
        for _, update_callback in self._bound_entities:
            update_callback(self._value)

import batFramework as bf


class ActionContainer:
    def __init__(self) -> None:
        self._actions: dict[str,bf.Action]= {}

    def clear(self):
        self._actions = {}

    def add_action(self, *actions:bf.Action):
        for action in actions:
            self._actions[action.get_name()] = action

    def has_action(self, name):
        return name in self._actions

    def is_active(self, name:str):
        return self._actions[name].is_active()

    def process_event(self, event):
        for action in self._actions.values():
            a = action.process_event(event) 
            if a and action._unique: break

    def reset(self):
        for action in self._actions.values():
            action.reset()

    def hard_reset(self):
        for action in self._actions.values():
            action.hard_reset()
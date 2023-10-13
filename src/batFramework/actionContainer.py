import batFramework as bf


class ActionContainer:
    def __init__(self, *actions: list[bf.Action]) -> None:
        self._actions: dict[str, bf.Action] = {}
        if actions:
            self.add_action(*actions)

    def clear(self):
        self._actions = {}

    def add_action(self, *actions: bf.Action):
        for action in actions:
            self._actions[action.get_name()] = action

    def get(self,name:str)->bf.Action:
        return self._actions.get(name)

    def has_action(self, name:str):
        return name in self._actions

    def is_active(self, *names:str)->bool:
        return all(self._actions.get(name).is_active() if name in self._actions else False for name in names)

    def process_event(self, event):
        for action in self._actions.values():
            a = action.process_event(event)
            if a and action._unique:
                break

    def reset(self):
        for action in self._actions.values():
            action.reset()

    def hard_reset(self):
        for action in self._actions.values():
            action.hard_reset()

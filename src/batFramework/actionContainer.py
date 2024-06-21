import batFramework as bf
import pygame


class ActionContainer:
    def __init__(self, *actions: list[bf.Action]) -> None:
        self._actions: dict[str, bf.Action] = {}
        if actions:
            self.add_actions(*actions)

    def __iter__(self):
        return iter(self._actions.values())

    def clear(self):
        self._actions = {}

    def add_actions(self, *actions: bf.Action):
        for action in actions:
            self._actions[action.name] = action

    def get(self, name: str) -> bf.Action:
        return self._actions.get(name)

    def has_action(self, name: str):
        return name in self._actions

    def get_all(self) -> list[bf.Action]:
        return self._actions

    def is_active(self, *names: str) -> bool:
        return all(
            self._actions.get(name).active if name in self._actions else False
            for name in names
        )

    def process_event(self, event):
        if event.consumed : return
        for action in self._actions.values():
            action.process_event(event)
            if event.consumed == True:break
             
    def reset(self):
        for action in self._actions.values():
            action.reset()

    def hard_reset(self):
        for action in self._actions.values():
            action.hard_reset()


class DirectionalKeyControls(ActionContainer):
    def __init__(self):
        super().__init__(
            bf.Action("up").add_key_control(pygame.K_UP).set_holding(),
            bf.Action("down").add_key_control(pygame.K_DOWN).set_holding(),
            bf.Action("left").add_key_control(pygame.K_LEFT).set_holding(),
            bf.Action("right").add_key_control(pygame.K_RIGHT).set_holding(),
        )


class WASDControls(ActionContainer):
    def __init__(self):
        super().__init__(
            bf.Action("up").add_key_control(pygame.K_w).set_holding(),
            bf.Action("down").add_key_control(pygame.K_s).set_holding(),
            bf.Action("left").add_key_control(pygame.K_a).set_holding(),
            bf.Action("right").add_key_control(pygame.K_d).set_holding(),
        )


class HybridControls(ActionContainer):
    def __init__(self):
        super().__init__(
            bf.Action("up").add_key_control(pygame.K_UP, pygame.K_w).set_holding(),
            bf.Action("down").add_key_control(pygame.K_DOWN, pygame.K_s).set_holding(),
            bf.Action("left").add_key_control(pygame.K_LEFT, pygame.K_a).set_holding(),
            bf.Action("right")
            .add_key_control(pygame.K_RIGHT, pygame.K_r)
            .set_holding(),
        )

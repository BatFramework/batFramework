from enum import Enum
import pygame

ActionType = Enum("type", "INSTANTANEOUS CONTINUOUS HOLDING")


# DEFAULT_KEY_REPEAT_PARAM = pygame.key.get_repeat()
class Action:
    def __init__(self, name: str) -> None:
        self._name = name
        self._active = False
        self._type = ActionType.INSTANTANEOUS
        self._key_control: list[int] = []
        self._mouse_control: list[int] = []
        self._gamepad_button_control: list[int] = []
        self._gamepad_axis_control: list[int] = []
        self._holding: list[int] = []
        self._unique = True
        self.data = None

    def set_unique(self, val: bool):
        self._unique = val

    def is_active(self):
        return self._active

    def set_active(self, value):
        self._active = value
        self._holding = []

    def add_key_control(self, *keys):
        for key in keys:
            if key not in self._key_control:
                self._key_control.append(key)
        return self

    def add_mouse_control(self, mouse):
        if mouse not in self._mouse_control:
            self._mouse_control.append(mouse)
        return self

    def get_name(self) -> str:
        return self._name

    def set_continuous(self) -> None:
        # pygame.key.set_repeat(DEFAULT_KEY_REPEAT_PARAM[0])
        self._holding = []
        self._type = ActionType.CONTINUOUS
        return self

    def is_continuous(self) -> bool:
        return self._type == ActionType.CONTINUOUS

    def set_instantaneous(self) -> None:
        # pygame.key.set_repeat(DEFAULT_KEY_REPEAT_PARAM[0])
        self._type = ActionType.INSTANTANEOUS
        self._holding = []
        return self

    def is_instantaneous(self) -> bool:
        return self._type == ActionType.INSTANTANEOUS

    def set_holding(self):
        # pygame.key.set_repeat(2)
        self._type = ActionType.HOLDING
        return self

    def is_holding_type(self):
        return self._type == ActionType.HOLDING

    def process_activate(self, event: pygame.Event) -> bool:
        if event.type == pygame.KEYDOWN and event.key in self._key_control:
            self._active = True
            # print(f"Action {self._name} activated by event ",event)
            if self.is_holding_type():
                self._holding.append(event.key)
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button in self._mouse_control:
            self._active = True
            if self.is_holding_type():
                self._holding.append(event.button)
            return True
        # TODO Add mouse motion actions
        if event.type == pygame.MOUSEMOTION and event.type in self._mouse_control:
            self._active = True
            if self.is_holding_type():
                self._holding.append(event.type)

        return False

    def process_update(self,event:pygame.Event)->None:
        if self.is_active() and self.is_holding_type() and pygame.MOUSEMOTION in self._mouse_control:
            self.value = {"pos":event.pos,"rel":event.rel}

    def process_deactivate(self, event: pygame.Event) -> bool:
        if self._type == ActionType.HOLDING:
            if event.type == pygame.KEYUP and event.key in self._key_control:
                if event.key in self._holding:
                    self._holding.remove(event.key)
                if self._holding == []:
                    self._active = False
                    return True
            elif (
                event.type == pygame.MOUSEBUTTONUP
                and event.button in self._mouse_control
            ):
                if event.button in self._holding:
                    self._holding.remove(event.button)
                if not self._holding:
                    self._active = False
                    return True
            elif (
                event.type == pygame.MOUSEMOTION
                and event.type in self._mouse_control
            ):
                self.value = None
                if event.type in self._holding:
                    self._holding.remove(event.type)
                if not self._holding:
                    self._active = False
                    return True
        return False

    def process_event(self, event: pygame.Event) -> bool:
        if not self._active:
            return self.process_activate(event)
        else:
            return self.process_deactivate(event)

    def reset(self):
        # if self._name == "click":print("RESET")

        if self._type in [ActionType.CONTINUOUS, ActionType.HOLDING]:
            return
        elif self._type == ActionType.INSTANTANEOUS:
            self._active = False

    def hard_reset(self):
        self._active = False
        self._holding = []

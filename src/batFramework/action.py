from typing import Any,Self
from enum import Enum
import pygame
from .enums import actionType



class Action:
    def __init__(self, name: str) -> None:
        """
        Create a new action with the given name.

        Args:
            name (str): The name of the action.
        """
        self.name: str = name
        self.active: bool = False
        self.data: dict = {}
        self.consume_event : bool = False
        self._type: actionType = actionType.INSTANTANEOUS
        self._key_control: set = set()
        self._mouse_control: set = set()
        self._event_control: set = set()
        self._gamepad_button_control: set = set()
        self._gamepad_axis_control: set = set()
        self._holding = set()

    def set_consume_event(self, val: bool) -> Self:
        """
        Set whether this action is unique (exclusive).
        When in an action Container, unique actions -when active - break the propagation of their event to other actions.

        Args:
            val (bool): True if the action is unique, False otherwise.
        """
        self.consume_event = val
        return self

    def set_active(self, value: bool) -> None:
        """
        Set the action's active state.

        Args:
            value (bool): True to activate the action, False to deactivate it.
        """
        self.active = value
        # self._holding = set()


    def add_event_control(self,*events)->Self:
        self._event_control.update(events)
        return self

    def remove_event_control(self,*events)->Self:
        self._event_control = self._event_control - events
        return self


    def add_key_control(self, *keys) -> Self:
        """
        Add key controls to the action.

        Args:
            *keys (int): Key codes to control this action.

        Returns:
            Action: The updated Action object for method chaining.
        """
        self._key_control.update(keys)
        return self

    def remove_key_control(self, *keys: int) -> Self:
        """
        Remove key controls to the action.

        Args:
            *keys (int): Key codes to control this action.

        Returns:
            Action: The updated Action object for method chaining.
        """
        self._key_control = self._key_control - set(keys)
        return self

    def replace_key_control(self, key, new_key) -> Self:
        if not key in self._key_control:
            return self
        self.remove_key_control(key)
        self.add_key_control(new_key)
        return self

    def add_mouse_control(self, *mouse_buttons: int) -> Self:
        """
        Add mouse control to the action.

        Args:
            *mouse_buttons (int): Mouse button codes to control this action.

        Returns:
            Action: The updated Action object for method chaining.
        """
        self._mouse_control.update(mouse_buttons)
        return self

    def set_continuous(self) -> Self:
        """
        Set the action type to continuous.

        Returns:
            Action: The updated Action object for method chaining.
        """
        self._holding = set()
        self._type = actionType.CONTINUOUS
        return self

    def is_continuous(self) -> bool:
        """
        Check if the action type is continuous.

        Returns:
            bool: True if the action type is continuous, False otherwise.
        """
        return self._type == actionType.CONTINUOUS

    def set_instantaneous(self) -> Self:
        """
        Set the action type to instantaneous.

        Returns:
            Action: The updated Action object for method chaining.
        """
        self._type = actionType.INSTANTANEOUS
        self._holding = set()
        return self

    def is_instantaneous(self) -> bool:
        """
        Check if the action type is instantaneous.

        Returns:
            bool: True if the action type is instantaneous, False otherwise.
        """
        return self._type == actionType.INSTANTANEOUS

    def set_holding(self) -> Self:
        """
        Set the action type to holding.

        Returns:
            Action: The updated Action object for method chaining.
        """
        self._type = actionType.HOLDING
        return self

    def is_holding_type(self) -> bool:
        """
        Check if the action type is holding.

        Returns:
            bool: True if the action type is holding, False otherwise.
        """
        return self._type == actionType.HOLDING

    def process_update(self, event: pygame.Event) -> None:
        if (
            event.type == pygame.MOUSEMOTION
            and self._type == actionType.HOLDING
            and pygame.MOUSEMOTION in self._mouse_control
        ) or self._event_control:
            self.data = event.dict

    def process_activate(self, event: pygame.event.Event):
        """
        Process activation of the action based on a pygame event.

        Args:
            event (pygame.event.Event): The pygame event to process.

        Returns:
            bool: True if the action was activated by the event, False otherwise.
        """

        if event.type == pygame.KEYDOWN and event.key in self._key_control:
            self._activate_action(event.key)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button in self._mouse_control:
            self._activate_action(event.button)

        elif event.type == pygame.MOUSEMOTION and event.type in self._mouse_control:
            self._activate_action(event.type)

        elif event.type in self._event_control:
            self._activate_action(event.type)
            self.data = event.dict
        else:
            return
        if self.consume_event : event.consumed = True

    def _activate_action(self, control):
        self.active = True
        if self._type == actionType.HOLDING:
            self._holding.add(control)

    def process_deactivate(self, event: pygame.event.Event):
        """
        Process deactivation of the action based on a pygame event.

        Args:
            event (pygame.event.Event): The pygame event to process.

        """
        if self._type == actionType.HOLDING:
            if event.type == pygame.KEYUP and event.key in self._key_control:
                self._deactivate_action(event.key)
            elif event.type == pygame.MOUSEBUTTONUP and event.button in self._mouse_control:
                self._deactivate_action(event.button)
            elif event.type == pygame.MOUSEMOTION and event.type in self._mouse_control:
                self._deactivate_action(event.type)
            elif event.type in self._event_control:
                self._deactivate_action(event.type)
            else:
                event.consumed = False

        if self.consume_event: event.consumed = True

    def _deactivate_action(self, control) -> bool:
        if control in self._holding:
            self._holding.remove(control)
        if not self._holding:
            self.active = False

    def process_event(self, event: pygame.event.Event):
        """
        Process a pygame event and update the action's state.

        Args:
            event (pygame.event.Event): The pygame event to process.
        """

        if event.consumed : return
        if not self.active:
            self.process_activate(event)
        else:
            self.process_deactivate(event)
        if self.active:
            self.process_update(event)
        return

    def reset(self) -> None:
        """
        Reset the action's state to the default state.
        """
        if self._type in {actionType.CONTINUOUS, actionType.HOLDING}:
            return
        elif self._type == actionType.INSTANTANEOUS:
            self.active = False

    def hard_reset(self) -> None:
        """
        Hard reset the action, deactivating it and clearing any holding controls.
        """
        self.active = False
        self._holding = set()

import batFramework as bf
import pygame
from batFramework.stateMachine import State,StateMachine
from ..animation import Animation
from ..animatedSprite import AnimatedSprite

class AnimatedState(State):

    def __init__(self, animation:str):
        super().__init__(animation)
        self._transition : dict[str,str] = {}
        self.animation = animation

    def add_transition(self,dest:str,transition_animation:str):
        self._transition[dest] = transition_animation


class AnimatedStateMachine(StateMachine):
    def __init__(self, parent:AnimatedSprite):
        self.states: dict[str, AnimatedState] = {}
        self.parent:AnimatedSprite = parent
        self.current_state = None

    def set_state(self, state_name: str,reset_counter:bool = True):

        if state_name not in self.states:
            return
            
        if self.current_state:
            self.current_state.on_exit()
        
        if self.current_state and state_name in self.current_state._transition:
            self.parent.set_animation(self.current_state._transition[state_name],reset_counter,0,self.states[state_name].animation)
        else:
            self.parent.set_animation(self.states[state_name].animation,reset_counter)

        self.current_state = self.states[state_name]
        self.current_state.on_enter()


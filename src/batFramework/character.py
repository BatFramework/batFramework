import batFramework as bf
from .stateMachine import State
from .animatedSprite import AnimatedSprite
from .dynamicEntity import DynamicEntity

class Character(AnimatedSprite,DynamicEntity):
    def __init__(self) -> None:
        super().__init__()
        self.state_machine = bf.StateMachine(self)
        self.do_setup_animations()
        self.do_setup_states()

    def set_state(self,state_name:str):
        self.state_machine.set_state(state_name)

    def get_current_state(self)->State:
        return self.state_machine.get_current_state()
    
    def update(self, dt: float) -> None:
        self.state_machine.update(dt)
        super().update(dt)

    def do_setup_states(self):
        pass
    
    def do_setup_animations(self):
        pass

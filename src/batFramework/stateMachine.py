import batFramework as bf


class StateMachine: ...


class State:
    def __init__(self, name: str) -> None:
        self.name = name
        self.parent: bf.Entity | bf.AnimatedSprite = None
        self.state_machine: StateMachine = None

    def set_parent(self, parent: bf.Entity | bf.AnimatedSprite):
        self.parent = parent

    def set_stateMachine(self, stateMachine):
        self.state_machine = stateMachine

    def update(self, dt):
        pass

    def on_enter(self):
        pass

    def on_exit(self):
        pass


class StateMachine:
    def __init__(self, parent) -> None:
        self.states: dict[str, State] = {}
        self.parent = parent
        self.current_state = None

    def add_state(self, state: State):
        self.states[state.name] = state
        state.set_parent(self.parent)
        state.set_stateMachine(self)

    def remove_state(self,state_name: str):
        self.states.pop(state_name,default=None)

    def set_state(self, state_name: str):
        if state_name in self.states:
            if self.current_state:
                self.current_state.on_exit()
            self.current_state = self.states[state_name]
            self.current_state.on_enter()

    def get_current_state(self) -> State:
        return self.current_state

    def update(self, dt):
        self.current_state.update(dt)

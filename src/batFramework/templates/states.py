import batFramework as bf
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .character import Platform2DCharacter


class CharacterState(bf.State):
    def set_parent(self, parent):
        """Initialize the parent character."""
        res = super().set_parent(parent)
        if res:
            self.parent: Platform2DCharacter = parent
        return res

    def on_enter(self):
        """Handle state entry."""
        self.parent.set_animation(self.name)

    def handle_input(self):
        """Process input and update movement direction."""
        if self.parent.actions.is_active("right"):
            self._apply_horizontal_input(self.parent.acceleration, self.parent.speed)
        if self.parent.actions.is_active("left"):
            self._apply_horizontal_input(-self.parent.acceleration, -self.parent.speed)

        if self.parent.velocity.x > 0:
            self.parent.set_flipX(False)
        elif self.parent.velocity.x < 0:
            self.parent.set_flipX(True)


    def _apply_horizontal_input(self, acceleration, limit):
        """Apply input acceleration and enforce speed limit."""

        self.parent.velocity.x += acceleration
        if abs(self.parent.velocity.x) > abs(limit):
            self.parent.velocity.x = limit

    def apply_friction(self):
        """Apply friction to horizontal velocity."""
        if (self.parent.actions.is_active("right") or self.parent.actions.is_active("left")):
            return
        
        if abs(self.parent.velocity.x) < 0.01:  # Threshold for negligible velocity
            self.parent.velocity.x = 0
        else:
            self.parent.velocity.x *= self.parent.friction

    def apply_gravity(self, dt):
        """Apply gravity to vertical velocity."""
        self.parent.velocity.y += self.parent.gravity * dt
        self.parent.velocity.y = min(self.parent.velocity.y, self.parent.terminal_velocity)

    def move_character(self, dt):
        """Move the character based on velocity."""
        self.parent.rect.x += self.parent.velocity.x * dt
        self.parent.rect.y += self.parent.velocity.y * dt

    def update(self, dt):
        """Update the character state."""
        self.handle_input()
        self.apply_physics(dt)
        self.handle_collision()

    def apply_physics(self, dt):
        """Apply all physics effects."""
        self.apply_friction()
        self.move_character(dt)
        if self.parent.on_ground:
            self.parent.velocity.y = 0  # Stop downward movement on ground

    def handle_collision(self):
        """Placeholder for collision detection and resolution."""
        pass  # Future collision code goes here


class Platform2DIdle(CharacterState):
    def __init__(self) -> None:
        super().__init__("idle")

    def on_enter(self):
        self.parent.jump_counter = 0
        super().on_enter()

    def update(self, dt):
        super().update(dt)
        
        if not self.parent.on_ground:
            self.parent.set_state("fall")
        elif self.parent.velocity.x != 0:
            self.parent.set_state("run")
        elif self.parent.actions.is_active("jump"):
            self.parent.set_state("jump")


class Platform2DRun(CharacterState):
    def __init__(self) -> None:
        super().__init__("run")


    def on_enter(self):
        self.parent.jump_counter = 0
        super().on_enter()

    def update(self, dt):
        super().update(dt)

        if self.parent.velocity.x :
            if (self.parent.actions.is_active("right") or self.parent.actions.is_active("left")):
                if self.parent.get_current_animation().name != "run" : self.parent.set_animation("run")
            else:
                if self.parent.get_current_animation().name != "idle" : self.parent.set_animation("idle")

        if self.parent.actions.is_active("jump"):
            self.parent.set_state("jump")
        elif self.parent.velocity.x == 0:
            if not (self.parent.actions.is_active("right") or self.parent.actions.is_active("left")):
                self.parent.set_state("idle")
        elif not self.parent.on_ground:
            self.parent.set_state("fall")

 


class Platform2DJump(CharacterState):
    def __init__(self) -> None:
        super().__init__("jump")

    def on_enter(self):
        super().on_enter()
        self.parent.on_ground = False
        self.parent.velocity.y = -self.parent.jump_force
        self.parent.jump_counter += 1

    def update(self, dt):
        super().update(dt)
        self.apply_gravity(dt)


        if self.parent.jump_counter < self.parent.max_jumps:
            if  self.parent.actions.is_active("jump") and (self.parent.velocity.y//10)*10 == 0:
                self.parent.set_state("jump")
                return


        if self.parent.velocity.y > 0:
            self.parent.set_state("fall")


class Platform2DFall(CharacterState):
    def __init__(self) -> None:
        super().__init__("fall")

    def update(self, dt):
        super().update(dt)
        self.apply_gravity(dt)

        if self.parent.on_ground:
            if abs(self.parent.velocity.x) > 0.01:
                self.parent.set_state("run")
            else:
                self.parent.set_state("idle")

        if self.parent.actions.is_active("jump") and self.parent.jump_counter < self.parent.max_jumps:
            self.parent.set_state("jump")
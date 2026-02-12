import pygame
import batFramework as bf
from typing import Self


class DynamicEntity(bf.Entity):
    def __init__(
        self,
        *args,**kwargs
    ) -> None:
        super().__init__(*args,**kwargs)
        self.velocity = pygame.math.Vector2(0, 0)
        self.ignore_collisions : bool = False
        self.grounded: bool = False  # Set by physics when standing on ground
        self._was_grounded: bool = False  # Previous frame grounded state
        self.mass : float = 1.0
        self.restitution : float = 0.5 # 1.0 is bouncy, 0.0 is not bouncy

    def on_collideX(self, collider: "bf.Entity") -> bool:
        """
        Called when colliding on X axis.
        
        Args:
            collider: The entity collided with
            
        Returns:
            True to keep velocity, False to zero velocity (default)
        """
        return False

    def on_collideY(self, collider: "bf.Entity") -> bool:
        """
        Called when colliding on Y axis.
        Override to add custom behavior (e.g., jump reset, damage).
        
        Args:
            collider: The entity collided with
            
        Returns:
            True to keep velocity, False to zero velocity (default)
        """
        # PhysicsWorld resets grounded=False at the start of each frame before
        # movement, so this runs only when a real ground collision is resolved.
        # _was_grounded holds last frame's value and is also set by PhysicsWorld.
        if self.velocity.y > 0:
            self.grounded = True
            if not self._was_grounded:
                self.on_land(collider)
        return False

    def on_land(self, collider: "bf.Entity") -> None:
        """
        Called when entity lands on something (transitions from falling to grounded).
        Override to add landing effects, sounds, etc.
        
        Args:
            collider: The entity landed on
        """
        pass

    def move_by_velocity(self, dt: float) -> None:
        """Move entity by its velocity * dt"""
        self.set_position(
            self.rect.x + self.velocity.x * dt, self.rect.y + self.velocity.y * dt
        )
    
    def apply_impulse(self, x: float, y: float) -> Self:
        """Add instantaneous velocity change"""
        self.velocity.x += x
        self.velocity.y += y
        return self
    
    def set_velocity(self, x: float | None = None, y: float | None = None) -> Self:
        """Set velocity components (None leaves component unchanged)"""
        if x is not None:
            self.velocity.x = x
        if y is not None:
            self.velocity.y = y
        return self
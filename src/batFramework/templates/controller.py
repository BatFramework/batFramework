import batFramework as bf
import pygame
from .stateMachine import *


class PlatformController(bf.DynamicEntity):
    """
    2D Platformer controller with proper physics.
    
    Physics model:
    - Acceleration applied based on input
    - Friction applied when no input (frame-rate independent)
    - Velocity clamped to max_speed
    - Gravity handled by PhysicsWorld
    - User has to define the minimum actions : `left`, `right` and `jump`
        and add them to the `control` ActionContainer
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.control = bf.ActionContainer()
        
        # Movement parameters
        self.max_speed = 200           # Maximum horizontal speed (pixels/sec)
        self.acceleration = 800        # Acceleration when moving (pixels/sec²)
        self.friction = 600            # Deceleration when no input (pixels/sec²)
        
        # Jump parameters
        self.jump_force = -400         # Initial jump velocity (pixels/sec)
        self.gravity = 800             # Handled by PhysicsWorld, but kept for reference
        self.terminal_velocity = 1000  # Max fall speed (pixels/sec)
        
        # Collision
        self.max_slope = 0
        
        # Internal state
        self._input_direction = 0  # -1, 0, or 1
        
    def reset_actions(self):
        self.control.reset()

    def process_actions(self, event):
        self.control.process_event(event)

    def update(self, dt):
        # Get input direction
        self._input_direction = 0
        if self.control.is_active("left"):
            self._input_direction -= 1
        if self.control.is_active("right"):
            self._input_direction += 1
        
        # Apply horizontal physics
        if self._input_direction != 0:
            # Accelerate in input direction
            target_velocity = self._input_direction * self.max_speed
            
            # Accelerate towards target
            if abs(self.velocity.x) < abs(target_velocity):
                # Speed up
                self.velocity.x += self._input_direction * self.acceleration * dt
                # Clamp to max speed
                if self._input_direction > 0:
                    self.velocity.x = min(self.velocity.x, self.max_speed)
                else:
                    self.velocity.x = max(self.velocity.x, -self.max_speed)
            else:
                # Already at/above target speed (direction change or speed boost)
                # Quickly adjust to target
                self.velocity.x = target_velocity
        else:
            # No input - apply friction
            if abs(self.velocity.x) > 0.01:
                # Apply friction as deceleration
                friction_force = self.friction * dt
                if abs(self.velocity.x) <= friction_force:
                    self.velocity.x = 0  # Stop if velocity would change sign
                else:
                    # Decelerate
                    sign = 1 if self.velocity.x > 0 else -1
                    self.velocity.x -= sign * friction_force
            else:
                self.velocity.x = 0
        
        # Jump
        if self.grounded and self.control.is_active("jump"):
            self.velocity.y = self.jump_force
            self.grounded = False
        
        # Clamp terminal velocity
        if self.velocity.y > self.terminal_velocity:
            self.velocity.y = self.terminal_velocity
        
        super().update(dt)


class TopDownController(bf.DynamicEntity):
    """
    Top-down controller with 8-directional movement and proper physics.
    
    Features:
    - Diagonal movement normalized correctly
    - Smooth acceleration/deceleration
    - Frame-rate independent friction
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.control = bf.ActionContainer()
        
        # Movement parameters
        self.max_speed = 300           # Maximum speed (pixels/sec)
        self.acceleration = 1200       # Acceleration (pixels/sec²)
        self.friction = 800            # Deceleration when no input (pixels/sec²)
        
        # Internal state
        self._input_vector = pygame.Vector2(0, 0)
        
    def reset_actions(self):
        self.control.reset()

    def process_actions(self, event):
        self.control.process_event(event)

    def update(self, dt):
        # Get input as a vector
        self._input_vector.update(0, 0)
        
        if self.control.is_active("left"):
            self._input_vector.x -= 1
        if self.control.is_active("right"):
            self._input_vector.x += 1
        if self.control.is_active("up"):
            self._input_vector.y -= 1
        if self.control.is_active("down"):
            self._input_vector.y += 1
        
        # Handle movement
        if self._input_vector.length_squared() > 0:
            # Normalize to prevent faster diagonal movement
            self._input_vector.normalize_ip()
            
            # Calculate target velocity
            target_velocity = self._input_vector * self.max_speed
            
            # Accelerate towards target velocity
            velocity_diff = target_velocity - self.velocity
            max_delta = self.acceleration * dt
            
            if velocity_diff.length_squared() > 0:
                # Accelerate in the direction of the difference
                if velocity_diff.length() <= max_delta:
                    # Can reach target this frame
                    self.velocity = target_velocity
                else:
                    # Accelerate by max amount
                    self.velocity += velocity_diff.normalize() * max_delta
        else:
            # No input - apply friction
            if self.velocity.length_squared() > 0.01:
                friction_magnitude = self.friction * dt
                
                if self.velocity.length() <= friction_magnitude:
                    # Stop completely
                    self.velocity.update(0, 0)
                else:
                    # Apply friction
                    friction_vector = self.velocity.normalize() * friction_magnitude
                    self.velocity -= friction_vector
            else:
                self.velocity.update(0, 0)
        
        # Ensure we don't exceed max speed (safety check)
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)
        
        super().update(dt)


class CameraController(bf.Entity):
    """
    Camera controller with mouse dragging and zooming.
    
    Controls:
    - Mouse drag: Pan camera
    - Scroll up/down: Zoom in/out
    - Ctrl + Scroll: Rotate camera
    """

    def __init__(self, *args, drag_mouse_button:int = 1, **kwargs):
        super().__init__(*args, **kwargs)
        self.origin = None  # Previous frame's world mouse pos
        self.mouse_actions = bf.ActionContainer(
            bf.Action("control").add_key_control(pygame.K_LCTRL).set_holding(),
            bf.Action("drag").add_mouse_control(drag_mouse_button).set_holding().set_consume_event(True),
            bf.Action("zoom_in").add_mouse_control(4).set_consume_event(True),
            bf.Action("zoom_out").add_mouse_control(5).set_consume_event(True),
        )

    def reset_actions(self):
        self.mouse_actions.reset()

    def process_actions(self, event):
        self.mouse_actions.process_event(event)
        if self.mouse_actions["drag"] and event.type == pygame.MOUSEMOTION:
            event.consumed = True
            pass

    def update(self, dt):
        cam = self.parent_layer.camera
        if self.mouse_actions["zoom_in"]:
            if self.mouse_actions["control"]:
                cam.rotate_by(10)
            else:
                cam.zoom(cam.zoom_factor * 1.1)

        elif self.mouse_actions["zoom_out"]:
            if self.mouse_actions["control"]:
                cam.rotate_by(-10)
            else:
                cam.zoom(cam.zoom_factor / 1.1)

        if self.mouse_actions["drag"]:
            mouse_world = cam.get_mouse_pos()
            cam_pos = cam.world_rect.topleft

            if self.origin is None:
                self.origin = (mouse_world[0] - cam_pos[0], mouse_world[1] - cam_pos[1])
            else:
                offset = (mouse_world[0] - cam_pos[0], mouse_world[1] - cam_pos[1])
                dx = offset[0] - self.origin[0]
                dy = offset[1] - self.origin[1]

                cam.move_by(-dx, -dy)
                self.origin = (mouse_world[0] - cam_pos[0], mouse_world[1] - cam_pos[1])

        else:
            self.origin = None
        self.do_update(dt)
        self.mouse_actions.reset()

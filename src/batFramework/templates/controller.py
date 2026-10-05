import batFramework as bf
import pygame
import math
from typing import Self
from .stateMachine import *


class PlatformController(bf.DynamicEntity):
    #TODO
    pass

class TopDownController(bf.DynamicEntity):
    """
    8-directional top-down movement, to mix with any Drawable subclass:

        class Player(bf.TopDownController, bf.Sprite): ...
        class Player(bf.AnimatedSprite, bf.TopDownController): ...  # also works

    Reads the "up", "down", "left" and "right" actions of self.controls,
    moves velocity toward direction * speed and moves the entity every
    update, before do_update.
    Speed is in pixels per second, acceleration/deceleration in pixels per
    second² (inf = instant, the default).

    """

    def __init__(
        self,
        *args,
        speed: float = 200.0,
        acceleration: float = float("inf"),
        deceleration: float = float("inf"),
        controls: bf.ActionContainer | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.controls: bf.ActionContainer = (
            controls if controls is not None else bf.DirectionalKeyControls()
        )
        self.speed: float = speed
        self.acceleration: float = acceleration
        self.deceleration: float = deceleration
        self.controls_enabled: bool = True
        self.input_direction = pygame.Vector2(0, 0)  # normalized, (0, 0) when idle
        self.facing = pygame.Vector2(0, 1)  # last non-zero input direction
        self._target_velocity = pygame.Vector2(0, 0)  # reused in update

    def set_speed(self, speed: float) -> Self:
        self.speed = speed
        return self

    def set_acceleration(self, acceleration: float) -> Self:
        self.acceleration = acceleration
        return self

    def set_deceleration(self, deceleration: float) -> Self:
        self.deceleration = deceleration
        return self

    def set_controls(self, controls: bf.ActionContainer) -> Self:
        """controls must contain "up", "down", "left" and "right" actions"""
        self.controls.hard_reset()
        self.controls = controls
        return self

    def set_controls_enabled(self, value: bool) -> Self:
        """When disabled, input is ignored and the entity decelerates to a stop"""
        self.controls_enabled = value
        return self

    @property
    def is_moving(self) -> bool:
        return self.velocity.x != 0 or self.velocity.y != 0

    # inputs are always tracked (even when disabled) so held keys stay in sync
    def process_actions(self, event: pygame.Event) -> None:
        super().process_actions(event)
        self.controls.process_event(event)

    def reset_actions(self) -> None:
        super().reset_actions()
        self.controls.reset()

    def do_when_removed(self):
        # key releases won't be received anymore
        self.controls.hard_reset()
        super().do_when_removed()

    def update_input_direction(self) -> None:
        direction = self.input_direction
        direction.update(0, 0)
        if self.controls_enabled:
            controls = self.controls
            direction.x = bool(controls["right"]) - bool(controls["left"])
            direction.y = bool(controls["down"]) - bool(controls["up"])
        if direction.x or direction.y:
            direction.normalize_ip()
            self.facing.update(direction)

    def update_movement(self, dt: float) -> None:
        self.update_input_direction()
        moving = self.input_direction.x or self.input_direction.y
        target = self._target_velocity
        target.update(self.input_direction)
        target *= self.speed

        rate = self.acceleration if moving else self.deceleration
        if math.isinf(rate):
            self.velocity.update(target)
        else:
            self.velocity.move_towards_ip(target, rate * dt)

        if self.is_moving:
            self.move_by_velocity(dt)

    def update(self, dt: float) -> None:
        self.update_movement(dt)
        # continue the chain (do_update, reset_actions, animations of the Drawable...)
        super().update(dt)


class CameraController(bf.Entity):
    """
    Camera controller with mouse dragging and zooming.

    Controls:
    - Mouse drag: Pan camera
    - Scroll up/down: Zoom in/out
    - Ctrl + Scroll: Rotate camera
    """

    def __init__(self, layer = bf.Layer.WORLD, *args, drag_mouse_button: int = 1, **kwargs):
        super().__init__(*args, **kwargs)
        self.origin = None  # Previous frame's world mouse pos
        self.mouse_actions = bf.ActionContainer(
            bf.Action("control").add_key_control(pygame.K_LCTRL).set_holding(),
            bf.Action("drag")
            .add_mouse_control(drag_mouse_button)
            .set_holding()
            .set_consume_event(True),
            bf.Action("zoom_in").add_mouse_control(4).set_consume_event(True),
            bf.Action("zoom_out").add_mouse_control(5).set_consume_event(True),
        )
        self.layer = layer

    def reset_actions(self):
        self.mouse_actions.reset()

    def process_actions(self, event):
        self.mouse_actions.process_event(event)
        if self.mouse_actions["drag"] and event.type == pygame.MOUSEMOTION:
            event.consumed = True
            pass

    def update(self, dt):
        cam = self.parent_scene.get_camera(self.layer)
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

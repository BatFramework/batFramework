import batFramework as bf
import pygame
from .stateMachine import *



class PlatformController(bf.DynamicEntity):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.control = bf.ActionContainer()
        self.speed = 300
        self.acceleration = 100
        self.jump_force = -400
        self.gravity = 800
        self.terminal_velocity = 1000
        self.on_ground = False
        self.friction = 0.7
        self.collision_rect = pygame.FRect(0,0,1,1)
        self.max_slope = 0
        
    def reset_actions(self):
        self.control.reset()

    def process_actions(self, event):
        self.control.process_event(event)

    def check_collision_y(self):
        pass

    def check_collision_x(self):
        pass

    def update(self, dt):
        super().update(dt)
        if (not self.control.is_active("right")) and (not self.control.is_active("left")):
            self.velocity.x *= self.friction
        if abs(self.velocity.x) <= 0.01:
            self.velocity.x = 0
        if not self.on_ground:
            self.velocity.y += self.gravity * dt
            if self.velocity.y > self.terminal_velocity:
                self.velocity.y = self.terminal_velocity
        if self.control.is_active("left"):
            self.velocity.x -= self.acceleration
        if self.control.is_active("right"):
            self.velocity.x += self.acceleration
        if self.on_ground and self.control.is_active("jump") :
            self.velocity.y = self.jump_force
            self.on_ground = False
        
        self.velocity.x = pygame.math.clamp(self.velocity.x,-self.speed,self.speed)
        self.collision_rect.x += self.velocity.x * dt
        self.check_collision_x()
        self.collision_rect.y += self.velocity.y * dt
        self.check_collision_y()



class TopDownController(bf.DynamicEntity):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.control = bf.ActionContainer()
        self.input_velocity = pygame.Vector2()
        self.speed = 500
        self.acceleration = 100
        self.friction = 0
        
    def reset_actions(self):
        self.control.reset()

    def process_actions(self, event):
        self.control.process_event(event)

    def check_collision_y(self):
        pass

    def check_collision_x(self):
        pass

    def update(self, dt):
        super().update(dt)
        self.input_velocity.update(0,0)
        self.velocity *= self.friction
        
        if abs(self.velocity.x) <= 0.01:
            self.velocity.x = 0
        if self.control.is_active("left"):
            self.input_velocity[0] = -self.acceleration
        if self.control.is_active("right"):
            self.input_velocity[0] =  self.acceleration
        if self.control.is_active("up"):
            self.input_velocity[1] = -self.acceleration
        if self.control.is_active("down"):
            self.input_velocity[1] =  self.acceleration

        if self.input_velocity:
            self.input_velocity.normalize_ip()

        self.velocity += self.input_velocity * self.acceleration
        self.velocity.clamp_magnitude_ip(self.speed)


        self.rect.x += self.velocity.x * dt
        self.check_collision_x()
        self.rect.y += self.velocity.y * dt
        self.check_collision_y()




class CameraController(bf.Entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.origin = None  # Previous frame's world mouse pos
        self.mouse_actions = bf.ActionContainer(
            bf.Action("control").add_key_control(pygame.K_LCTRL).set_holding(),
            bf.Action("drag").add_mouse_control(1).set_holding().set_consume_event(True),
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

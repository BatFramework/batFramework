import batFramework as bf
import pygame

class PlatformController(bf.DynamicEntity):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.control = bf.ActionContainer()
        self.speed = 500
        self.acceleration = 100
        self.jump_force = -500
        self.gravity = 1200
        self.on_ground = False
        self.friction = 0.7
        
    def do_reset_actions(self):
        self.control.reset()

    def do_process_actions(self, event):
        self.control.process_event(event)

    def check_collision_y(self):
        pass

    def check_collision_x(self):
        pass

    def update(self, dt):
        super().update(dt)
        self.velocity.x *= self.friction
        if abs(self.velocity.x) <= 0.01:
            self.velocity.x = 0
        if not self.on_ground:
            self.velocity.y += self.gravity * dt
        if self.control.is_active("left"):
            self.velocity.x -= self.acceleration
        if self.control.is_active("right"):
            self.velocity.x += self.acceleration
        if self.on_ground and self.control.is_active("jump") :
            self.velocity.y = self.jump_force
            self.on_ground = False
        
        self.velocity.x = pygame.math.clamp(self.velocity.x,-self.speed,self.speed)
        self.rect.x += self.velocity.x * dt
        self.check_collision_x()
        self.rect.y += self.velocity.y * dt
        self.check_collision_y()



class TopDownController(bf.DynamicEntity):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.control = bf.ActionContainer()
        self.input_velocity = pygame.Vector2()
        self.speed = 500
        self.acceleration = 100
        self.friction = 0
        
    def do_reset_actions(self):
        self.control.reset()

    def do_process_actions(self, event):
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

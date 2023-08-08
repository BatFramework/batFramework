import batFramework as bf
import pygame
from pygame.math import Vector2

class Particle:

    def __init__(self,start_pos:tuple[float,float],start_vel:tuple[float,float],duration=1000,color=None):
        self.rect = pygame.FRect(*start_pos,0,0)
        self.surface = pygame.Surface((4,4)).convert()
        if color : self.surface.fill(color)
        self.velocity = Vector2(*start_vel)
        self.start_time = pygame.time.get_ticks()
        self.duration = duration
        self.dead = False
        self.progression = 0
    def update(self,dt):
        elapsed_time = pygame.time.get_ticks() - self.start_time
        self.progression = elapsed_time / self.duration
        self.surface.set_alpha(255-int(self.progression * 255))
        self.dead = elapsed_time >= self.duration 
        self.rect.center += self.velocity * dt

class ParticleManager(bf.Entity):
    def __init__(self) -> None:
        super().__init__(size=bf.const.RESOLUTION)
        self.particles :list[Particle] = []

    def get_bounding_box(self):
        for particle in self.particles:
            yield particle.rect
    def add_particle(self,**kwargs):
        self.particles.append(Particle(**kwargs))

    def update(self, dt: float):
        particles_to_remove = []
        for particle in self.particles:
            particle.update(dt)
            if particle.dead:
                particles_to_remove.append(particle)
        for p in particles_to_remove : self.particles.remove(p)

    def draw(self, camera) -> bool:
        camera.surface.fblits([(p.surface,camera.transpose(p.rect).topleft) for p in self.particles])
        return len(self.particles)
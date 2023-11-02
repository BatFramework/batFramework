import batFramework as bf
import pygame
from pygame.math import Vector2


class Particle:
    def __init__(
        self,
        start_pos: tuple[float, float],
        start_vel: tuple[float, float],
        duration=1000,
        color=None,
        size = (4,4)
    ):
        self.rect = pygame.FRect(*start_pos, 0, 0)
        self.surface = pygame.Surface(size).convert()
        if color:
            self.surface.fill(color)
        self.velocity = Vector2(*start_vel)
        self.start_time = pygame.time.get_ticks()
        self.duration = duration
        self.dead = False
        self.progression = 0
        self.z_depth = 1

    def update(self, dt):
        if self.dead:
            return
        elapsed_time = pygame.time.get_ticks() - self.start_time
        self.progression = elapsed_time / self.duration
        self.dead = elapsed_time >= self.duration
        self.rect.center += self.velocity * dt
        self.update_surface()

    def kill(self):
        self.dead = True

    def update_surface(self):
        self.surface.set_alpha(255 - int(self.progression * 255))


class ParticleManager(bf.Entity):
    def __init__(self) -> None:
        super().__init__(size=bf.const.RESOLUTION)
        self.particles: list[Particle] = []

    def get_bounding_box(self):
        for particle in self.particles:
            yield particle.rect

    def add_particle(self, particle_class=Particle, **kwargs):
        self.particles.append(particle_class(**kwargs))


    def clear(self):
        self.particles = []
        

    def update(self, dt: float):
        particles_to_remove = []
        for particle in self.particles:
            particle.update(dt)
            if particle.dead:
                particles_to_remove.append(particle)
        for p in particles_to_remove:
            self.particles.remove(p)

    def draw(self, camera) -> bool:
        camera.surface.fblits(
            [
                (
                    p.surface,
                    tuple(round(i * self.z_depth) for i in camera.transpose(self.rect).topleft)
                ) for p in self.particles
            ]
        )
        return len(self.particles)

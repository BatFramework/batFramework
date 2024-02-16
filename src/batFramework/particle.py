import batFramework as bf
import pygame
from pygame.math import Vector2


class Particle:
    def __init__(self, *args, **kwargs):
        self.dead = False
        self.surface = None

    def update(self,dt):pass
    
    def kill(self):
        self.dead = True

    def update_surface(self):
        pass


class TimedParticle(Particle):
    def __init__(self, duration):
        super().__init__()
        self.timer = bf.Timer(duration,end_callback = self.kill).start()


class BasicParticle(TimedParticle):
    def __init__(
        self,
        start_pos: tuple[float, float],
        start_vel: tuple[float, float],
        duration=1,
        color=None,
        size=(4, 4),
    ):
        super().__init__(duration)
        self.rect = pygame.FRect(*start_pos, 0, 0)
        self.surface = pygame.Surface(size).convert()
        if color:
            self.surface.fill(color)
        self.velocity = Vector2(start_vel)

    def update(self, dt):
        super().update(dt)
        self.rect.center += self.velocity * dt
        self.update_surface()

    def update_surface(self):
        self.surface.set_alpha(255 - int(self.timer.get_progression() * 255))


class ParticleGenerator(bf.Entity):
    def __init__(self) -> None:
        super().__init__(size=bf.const.RESOLUTION)
        self.particles: list[Particle] = []

    def get_bounding_box(self):
        for particle in self.particles:
            yield particle.rect
        yield self.rect

    def add_particle(self, particle=Particle):
        self.particles.append(particle)

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
                (p.surface,camera.transpose(p.rect).topleft)
                for p in self.particles
            ]
        )
        return len(self.particles)

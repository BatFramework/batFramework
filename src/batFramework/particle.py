import batFramework as bf
import pygame
from pygame.math import Vector2


class Particle:
    def __init__(self, *args, **kwargs):
        self.dead = False
        self.surface = None
        self.generator = None

    def do_when_added(self):
        pass

    def update(self, dt):
        pass

    def kill(self):
        self.dead = True

    def update_surface(self):
        pass


class TimedParticle(Particle):
    def __init__(self, duration):
        super().__init__()
        self.duration = duration

    def do_when_added(self):
        if self.generator and self.generator.parent_scene:
            self.timer = bf.SceneTimer(
                self.duration, end_callback=self.kill,
                scene_name=self.generator.parent_scene.name).start()        
        else:
            self.timer = bf.Timer(self.duration, end_callback=self.kill).start()


class BasicParticle(TimedParticle):
    def __init__(
        self,
        start_pos: tuple[float, float],
        start_vel: tuple[float, float],
        duration=1,
        color=None,
        size: tuple[int, int] = (4, 4),
        *args,
        **kwargs,
    ):
        super().__init__(duration)
        self.rect = pygame.FRect(0,0, *size)
        self.rect.center = start_pos
        self.surface = pygame.Surface(size)
        self.velocity = Vector2(start_vel)
        if color:
            self.surface.fill(color)
        self.start()

    def start(self):
        pass

    def update(self, dt):
        super().update(dt)
        self.rect.center += self.velocity * dt
        self.update_surface()

    def update_surface(self):
        self.surface.set_alpha(255 - int(self.timer.get_progression() * 255))


class DirectionalParticle(BasicParticle):
    def start(self):
        self.original_surface = self.surface.copy()

    def update_surface(self):
        angle = self.velocity.angle_to(Vector2(1, 0))
        self.surface = pygame.transform.rotate(self.original_surface, angle)
        super().update_surface()


class ParticleGenerator(bf.Drawable):
    def __init__(self) -> None:
        super().__init__((0, 0))
        self.particles: list[Particle] = []

    def get_debug_outlines(self):
        return
        for particle in self.particles:
            yield (
                particle.rect.move(particle.rect.w // 2, particle.rect.h // 2),
                "blue",
            )
        yield (self.rect, "cyan")

    def add_particle(self, particle:Particle):
        particle.generator = self
        particle.do_when_added()
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

    def draw(self, camera) -> None:
        camera.surface.fblits(
            [(p.surface, camera.world_to_screen(p.rect)) for p in self.particles]
        )

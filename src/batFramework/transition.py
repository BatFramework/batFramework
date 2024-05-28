import batFramework as bf
from typing import Self
import pygame

"""
Both surfaces to transition need to be the same size

"""


class Transition:
    def __init__(
        self, duration: float, easing_function: bf.easing = bf.easing.LINEAR
    ) -> None:
        """
        duration : time in seconds
        easing function : controls the progression rate
        """
        self.duration: float = duration
        self.controller = bf.EasingController(
            easing_function,
            duration,
            update_callback=self.update,
            end_callback=self.end,
        )
        self.start_callback = None
        self.update_callback = None
        self.end_callback = None
        self.source: pygame.Surface = None
        self.dest: pygame.Surface = None

    def __repr__(self) -> str:
        return f"Transition {self.__class__},{self.duration}"

    def set_start_callback(self, func) -> Self:
        self.start_callback = func
        return self

    def set_update_callback(self, func) -> Self:
        self.update_callback = func
        return self

    def set_end_callback(self, func) -> Self:
        self.end_callback = func
        return self

    def set_source(self, surface: pygame.Surface) -> None:
        self.source = surface

    def set_dest(self, surface: pygame.Surface) -> None:
        self.dest = surface

    def start(self):
        if self.controller.has_started():
            return
        if self.duration:
            self.controller.start()
            if self.start_callback:
                self.start_callback()
            return

        self.controller.start()
        if self.start_callback:
            self.start_callback()
        self.controller.end()
        self.update(1)
        self.end()

    def update(self, progression: float) -> None:
        if self.update_callback:
            self.update_callback(progression)

    def end(self):
        self.controller.stop()
        if self.end_callback:
            self.end_callback()

    def draw(self, surface: pygame.Surface) -> None:
        pass

    def skip(self, no_callback: bool = False):
        self.controller.stop()
        if self.end_callback and (no_callback == False):
            self.end_callback()


class FadeColor(Transition):
    def __init__(
        self,
        color: tuple | str,
        middle_duration: float,
        first_duration: float = None,
        second_duration: float = None,
        easing_function: bf.easing = bf.easing.LINEAR,
    ) -> None:
        super().__init__(0, easing_function)
        if first_duration is None:
            first_duration = middle_duration
        if second_duration is None:
            second_duration = middle_duration
        self.index = 0
        self.first = Fade(first_duration)
        self.color = color
        self.second = Fade(second_duration).set_end_callback(
            lambda: self.next_step(self.end)
        )
        self.timer = bf.Timer(
            middle_duration, lambda: self.next_step(self.second.start)
        )
        self.first.set_end_callback(lambda: self.next_step(self.timer.start))

    def next_step(self, callback=None) -> None:
        self.index += 1
        if callback:
            callback()

    def set_source(self, surface) -> None:
        super().set_source(surface)
        self.first.set_source(surface)

    def set_dest(self, surface) -> None:
        super().set_dest(surface)
        self.second.set_dest(surface)

    def start(self):
        if self.start_callback:
            self.start_callback()
        self.color_surf = pygame.Surface(self.source.get_size())
        self.color_surf.fill(self.color)

        self.first.set_dest(self.color_surf)
        self.second.set_source(self.color_surf)
        self.first.start()

    def draw(self, surface):
        if self.index == 0:
            self.first.draw(surface)
        elif self.index == 1:
            surface.blit(self.color_surf, (0, 0))
        else:
            self.second.draw(surface)

    def skip(self, no_callback: bool = False):
        if (no_callback == False) and self.end_callback:
            self.end_callback()

        self.first.controller.stop()
        self.timer.stop()
        self.second.controller.stop()


class Fade(Transition):
    def end(self):
        self.dest.set_alpha(255)
        return super().end()

    def draw(self, surface):
        dest_alpha = 255 * self.controller.get_value()
        self.dest.set_alpha(dest_alpha)
        surface.blit(self.source, (0, 0))
        surface.blit(self.dest, (0, 0))


class GlideRight(Transition):
    def draw(self, surface):
        width = surface.get_width()
        source_x = -self.controller.get_value() * width
        surface.blit(self.source, (source_x, 0))
        surface.blit(self.dest, (width + source_x, 0))


class GlideLeft(Transition):
    def draw(self, surface):
        width = surface.get_width()
        source_x = self.controller.get_value() * width
        surface.blit(self.source, (source_x, 0))
        surface.blit(self.dest, (source_x - width, 0))


class CircleOut(Transition):
    def start(self):
        super().start()
        self.circle_surf = self.source.copy()
        self.circle_surf.set_colorkey((0, 0, 0))
        self.circle_surf.fill((0, 0, 0))
        self.surface_width = self.circle_surf.get_width()

    def draw(self, surface):
        v = self.controller.get_value()

        radius = self.surface_width * v
        pygame.draw.circle(
            self.circle_surf, "white", self.circle_surf.get_rect().center, radius
        )
        mask = pygame.mask.from_surface(self.circle_surf)
        mask.to_surface(surface=surface, setsurface=self.dest, unsetsurface=self.source)


class CircleIn(Transition):
    def start(self):
        super().start()
        self.circle_surf = self.source.copy()
        self.circle_surf.set_colorkey((0, 0, 0))
        self.circle_surf.fill((0, 0, 0))
        self.surface_width = self.circle_surf.get_width()

    def draw(self, surface):
        v = self.controller.get_value()
        radius = self.surface_width - (self.surface_width * v)
        self.circle_surf.fill((0, 0, 0))
        pygame.draw.circle(
            self.circle_surf, "white", self.circle_surf.get_rect().center, radius
        )
        mask = pygame.mask.from_surface(self.circle_surf)
        mask.to_surface(surface=surface, setsurface=self.source, unsetsurface=self.dest)

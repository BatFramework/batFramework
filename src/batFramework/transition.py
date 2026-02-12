import batFramework as bf
from typing import Self,Callable,Any
import pygame

"""
Both surfaces to transition need to be the same size

"""


class Transition:
    def __init__(
        self, duration: float=1, easing: bf.easing = bf.easing.LINEAR
    ) -> None:
        """
        duration : time in seconds
        easing function : controls the progression rate
        """
        self.duration: float = duration
        self.controller = bf.EasingController( # main controller for the transition progression
            duration,easing,
            update_callback=self.update,end_callback=self.end,
        )
        self.source: pygame.Surface = None
        self.dest: pygame.Surface = None
        self.is_over : bool = False # this flag tells the manager the transition is over 

    def __repr__(self) -> str:
        return f"Transition ({self.__class__},{self.duration})"

    def set_source(self, surface: pygame.Surface) -> None:
        self.source = surface

    def set_dest(self, surface: pygame.Surface) -> None:
        self.dest = surface

    def start(self):
        if self.controller.has_started(): # can't start again while it's in progress 
            return
        if self.duration: # start the transition
            self.controller.start()
            return

        # if no duration the transition is instantaneous
        self.controller.start()
        self.controller.end()
        self.update(1)# to prevent weird behaviour, update once with progression at max value
        self.end()

    def update(self, progression: float) -> None:
        pass

    def end(self):
        self.controller.stop()
        self.is_over = True

    def draw(self, surface: pygame.Surface) -> None:
        pass

    def skip(self):
        self.end()



class FadeColor(Transition):
    def __init__(self,duration:float,color=(0,0,0),color_start:float=0.3,color_end:float=0.7, easing = bf.easing.LINEAR):
        super().__init__(duration, easing)
        self.color = color
        self.color_start = color_start
        self.color_end = color_end

    def start(self):
        super().start()
        self.color_surf = pygame.Surface(self.source.get_size())
        self.color_surf.fill(self.color)

    def draw(self, surface):
        v = self.controller.get_value()
        if v < self.color_start:
            v = v/(self.color_start)
            self.color_surf.set_alpha(255*v)
            surface.blit(self.source)
            surface.blit(self.color_surf)

        elif v < self.color_end:
            self.color_surf.set_alpha(255)
            surface.blit(self.color_surf)

        else:
            v = (v-self.color_end)/(1-self.color_end)
            surface.blit(self.color_surf)
            self.dest.set_alpha(255*v)
            surface.blit(self.dest)

class Fade(Transition):
    def end(self):
        self.dest.set_alpha(255)
        return super().end()

    def start(self):
        super().start()

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



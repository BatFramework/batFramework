import batFramework as bf 
from typing import Self
import pygame

"""
Both surfaces to transition need to be the same size

"""

class Transition:
    def __init__(self, duration:float, easing_function:bf.easing = bf.easing.LINEAR)->None:
        self.duration = duration
        self.controller = bf.EasingController(easing_function, duration, update_callback = self.update, end_callback=self.end)
        self.start_callback=None
        self.update_callback=None
        self.end_callback = None
        self.source = None
        self.dest = None


    def set_start_callback(self,func)->Self:
        self.start_callback = func
        return self
        
    def set_update_callback(self,func)->Self:
        self.update_callback = func
        return self
        
    def set_end_callback(self,func)->Self:
        self.end_callback = func
        return self   

    def set_source(self,surface)->None:
        self.source =surface
        
    def set_dest(self,surface)->None:
        self.dest = surface

    def start(self):
        if self.controller.has_started() : return
        self.controller.start()
        if self.start_callback:  self.start_callback()
    
    def update(self,progression:float)->None:
        if self.update_callback: self.update_callback()

    def end(self):
        if self.end_callback: self.end_callback()
        pass

    def draw(self,surface)->None:
        pass


class Fade(Transition):
    def draw(self,surface):
        dest_alpha = 255 * self.controller.get_value()
        self.dest.set_alpha(dest_alpha)
        surface.blit(self.source,(0,0))
        surface.blit(self.dest,(0,0))


class GlideRight(Transition):
    def draw(self,surface):
        width = surface.get_width()
        source_x = - self.controller.get_value() * width
        surface.blit(self.source,(source_x,0))
        surface.blit(self.dest,(width+source_x,0))

class GlideLeft(Transition):
    def draw(self,surface):
        width = surface.get_width()
        source_x = self.controller.get_value() * width
        surface.blit(self.source,(source_x,0))
        surface.blit(self.dest,(source_x-width,0))


class CircleOut(Transition):
    def start(self):
        super().start()
        self.circle_surf = self.source.copy()
        self.circle_surf.set_colorkey((0,0,0))
        self.circle_surf.fill((0,0,0))
        self.surface_width = self.circle_surf.get_width() 
    def draw(self,surface):
        v = self.controller.get_value()

        radius = (self.surface_width * v)
        pygame.draw.circle(self.circle_surf,"white",self.circle_surf.get_rect().center,radius)
        mask = pygame.mask.from_surface(self.circle_surf)
        mask.to_surface(surface=surface,setsurface=self.dest,unsetsurface=self.source)


class CircleIn(Transition):
    def start(self):
        super().start()
        self.circle_surf = self.source.copy()
        self.circle_surf.set_colorkey((0,0,0))
        self.circle_surf.fill((0,0,0))
        self.surface_width = self.circle_surf.get_width() 

    def draw(self,surface):
        v = self.controller.get_value()
        radius = self.surface_width -  (self.surface_width * v) 
        self.circle_surf.fill((0,0,0))
        pygame.draw.circle(self.circle_surf,"white",self.circle_surf.get_rect().center,radius)
        mask = pygame.mask.from_surface(self.circle_surf)
        mask.to_surface(surface=surface,setsurface=self.source,unsetsurface=self.dest)



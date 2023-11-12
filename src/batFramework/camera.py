import batFramework as bf
import pygame
from pygame.math import Vector2


class Camera:
    def __init__(self, flags=0) -> None:
        self.rect = pygame.FRect(0, 0, *bf.const.RESOLUTION)
        self.flags: int = flags
        # self.blit_special_flags : int =pygame.BLEND_PREMULTIPLIED if (flags & pygame.SRCALPHA) else 0
        self.blit_special_flags: int = pygame.BLEND_ALPHA_SDL2
        self._clear_color : pygame.Color = pygame.Color(0, 0, 0, 0)
        self.zoom_factor = 1
        self.cached_surfaces: dict[float, pygame.Surface] = {}
        self.surface: pygame.Surface = pygame.Surface((0,0))
        self.follow_point_func = None
        self.max_zoom = 2
        self.min_zoom = 0.1
        self.zoom(1)

    def set_clear_color(self, color: pygame.Color|tuple):
        if not isinstance(color,pygame.Color):
            color = pygame.Color(color)
        self._clear_color = color

    def set_max_zoom(self,value:float):
        self.max_zoom = value

    def set_min_zoom(self,value:float):
        self.min_zoom = value

    def clear(self):
        """
        Clear the camera surface with the set clear color
        (default is tranparent)
        """
        self.surface.fill(self._clear_color)

    def get_center(self):
        return self.rect.center

    

    def move(self, x, y):
        """
        Moves the camera rect by the given coordinates (+=)
        """
        self.rect.topleft += Vector2(x, y)

    def set_position(self, x, y):
        """
        Set the camera rect topleft position
        """
        self.rect.topleft = (x, y)

    def set_center(self, x, y):
        """
        Set the camera rect center position
        """
        self.rect.center = (x, y)

    def set_follow_dynamic_point(self, func):
        """
        Set the following function (returns tuple x y)
        (camera will center its position to the center of the given coordinates)
        """
        self.follow_point_func = func

    def zoom_by(self, amount:float):
        self.zoom(self.zoom_factor + amount)

    def zoom(self, factor):
        if factor <self.min_zoom:
            return
        if factor > self.max_zoom:
            return
        factor = round(factor,2)
        self.zoom_factor = factor
        if factor not in self.cached_surfaces:
            # if factor != 1 : print("creating new surface in cache : ",tuple(i * factor for i in const.RESOLUTION), self.flags)
            self.cached_surfaces[factor] = pygame.Surface(
                tuple(i / factor for i in bf.const.RESOLUTION), flags=self.flags
            ).convert_alpha()
            # c = self.surface.get_colorkey() if self.surface else None
            # if c : self.cached_surfaces[factor].set_colorkey(c)
            self.cached_surfaces[factor].fill((0, 0, 0, 0))

        self.surface = self.cached_surfaces[self.zoom_factor]
        self.rect = self.surface.get_frect(center=self.rect.center)
        # if factor != 1 : print(self.cached_surfaces)

    def intersects(self, rect: pygame.Rect | pygame.FRect) -> bool:
        return (
            self.rect.x < rect.right
            and self.rect.right > rect.x
            and self.rect.y < rect.bottom
            and self.rect.bottom > rect.y
        )


    def transpose(self, rect: pygame.Rect | pygame.FRect) -> pygame.Rect | pygame.FRect:
        x, y = round(rect.x - self.rect.left), round(rect.y - self.rect.top)
        return pygame.Rect(x, y, *rect.size)

    def convert_screen_to_world(self, x, y):
        return x / self.zoom_factor + self.rect.x, y / self.zoom_factor + self.rect.y

    def update(self, dt):
        if self.follow_point_func:
            target = self.follow_point_func()
            self.rect.center = Vector2(self.rect.center).lerp(target, ((dt * 60) * 0.1))

    def draw(self, surface: pygame.Surface):
        # pygame.draw.circle(surface,bf.color.ORANGE,self.surface.get_rect().center,4)
        if self.zoom_factor == 1:
            surface.blit(self.surface, (0, 0), special_flags=self.blit_special_flags)
            return
        # print("From",self.surface,"Target RESOLUTION",const.RESOLUTION,"Destination",surface)
        surface.blit(
            pygame.transform.scale(self.surface, bf.const.RESOLUTION),
            (0, 0),
            special_flags=self.blit_special_flags,
        )

import pygame
import batFramework as bf
import random
from .enums import *
import re
from typing import Callable, TYPE_CHECKING
from functools import cache
if TYPE_CHECKING:
    from .drawable import Drawable
    from .entity import Entity



class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Utils:

    @staticmethod
    def split_surface(
        surface: pygame.Surface, split_size: tuple[int, int], func=None
    ) -> dict[tuple[int, int], pygame.Surface]:
        """
        Splits a surface into subsurfaces based on a given size and returns a dictionary of them with their coordinates as keys.

        Args:
            surface (pygame.Surface): The surface to be split.
            split_size (tuple[int, int]): The size of each subsurface (width, height).
            func (callable, optional): A function to apply to each subsurface. Defaults to None.

        Returns:
            dict[tuple[int, int], pygame.Surface]: A dictionary with (x, y) coordinates as keys and the corresponding subsurfaces as values.
        """
        width, height = surface.get_size()
        res = {}
        for iy, y in enumerate(range(0, height, split_size[1])):
            for ix, x in enumerate(range(0, width, split_size[0])):
                sub = surface.subsurface((x, y, split_size[0], split_size[1]))

                if func is not None:
                    sub = func(sub)

                res[(ix, iy)] = sub

        return res

    @staticmethod
    def filter_text(text_mode: textMode):
        """
        Filters a string based on the specified text mode.

        Args:
            text_mode (textMode): Mode specifying the type of filtering (ALPHABETICAL, NUMERICAL, ALPHANUMERICAL).

        Returns:
            callable: A function that takes a string and removes all characters not allowed by the text mode.

        Raises:
            ValueError: If an unsupported text mode is provided.
        """

        if text_mode == textMode.ALPHABETICAL:
            pattern = re.compile(r"[^a-zA-Z]")
        elif text_mode == textMode.NUMERICAL:
            pattern = re.compile(r"[^0-9]")
        elif text_mode == textMode.ALPHANUMERICAL:
            pattern = re.compile(r"[^a-zA-Z0-9]")
        else:
            raise ValueError("Unsupported text mode")

        def filter_function(s: str) -> str:
            return pattern.sub("", s)

        return filter_function


    @staticmethod
    def create_spotlight(inside_color, outside_color, radius, radius_stop=None, dest_surf=None,size=None):
        """
        Creates a spotlight effect on a surface with a gradient from inside_color to outside_color.

        Args:
            inside_color (tuple[int, int, int]): RGB color at the center of the spotlight.
            outside_color (tuple[int, int, int]): RGB color at the outer edge of the spotlight.
            radius (int): Radius of the inner circle.
            radius_stop (int, optional): Radius where the spotlight ends. Defaults to the value of radius.
            dest_surf (pygame.Surface, optional): Surface to draw the spotlight on. Defaults to None.
            size (tuple[int, int], optional): Size of the surface if dest_surf is None. Defaults to a square based on radius_stop.

        Returns:
            pygame.Surface: The surface with the spotlight effect drawn on it.
        """

        if radius_stop is None:
            radius_stop = radius
        diameter = radius_stop * 2

        if dest_surf is None:
            if size is None:
                size = (diameter,diameter)
            dest_surf = pygame.Surface(size, pygame.SRCALPHA)
        
        dest_surf.fill((0,0,0,0))


        center = dest_surf.get_rect().center

        if radius_stop != radius:
            for r in range(radius_stop, radius - 1, -1):
                color = [
                    inside_color[i] + (outside_color[i] - inside_color[i]) * (r - radius) / (radius_stop - radius)
                    for i in range(3)
                ] + [255]  # Preserve the alpha channel as fully opaque
                pygame.draw.circle(dest_surf, color, center, r)
        else:
            pygame.draw.circle(dest_surf, inside_color, center, radius)

        return dest_surf

    @staticmethod
    def draw_spotlight(dest_surf:pygame.Surface,inside_color,outside_color,radius,radius_stop=None,center=None):
        """
        Draws a spotlight effect directly onto an existing surface.

        Args:
            dest_surf (pygame.Surface): The surface to draw the spotlight on.
            inside_color (tuple[int, int, int]): RGB color at the center of the spotlight.
            outside_color (tuple[int, int, int]): RGB color at the outer edge of the spotlight.
            radius (int): Radius of the inner circle.
            radius_stop (int, optional): Radius where the spotlight ends. Defaults to the value of radius.
            center (tuple[int, int], optional): Center point of the spotlight. Defaults to the center of dest_surf.
        """

        if radius_stop is None:
            radius_stop = radius
        center = dest_surf.get_rect().center if center is None else center
        if radius_stop != radius:
            for r in range(radius_stop, radius - 1, -1):
                color = [
                    inside_color[i] + (outside_color[i] - inside_color[i]) * (r - radius) / (radius_stop - radius)
                    for i in range(3)
                ] + [255]
                pygame.draw.circle(dest_surf, color, center, r)
        else:
            pygame.draw.circle(dest_surf, inside_color, center, radius)

    @staticmethod
    def animate_move(entity:"Entity", start_pos : tuple[float,float], end_pos:tuple[float,float])->Callable[[float],None]:
        """
        Creates a function to animate the movement of an entity from start_pos to end_pos.

        Args:
            entity (Entity): The entity to move.
            start_pos (tuple[float, float]): The starting position of the entity.
            end_pos (tuple[float, float]): The ending position of the entity.

        Returns:
            Callable[[float], None]: A function that updates the entity's position based on a progression value (0 to 1).
        """
        def func(x):
            entity.set_center(start_pos[0]+(end_pos[0]-start_pos[0])*x,start_pos[1]+(end_pos[1]-start_pos[1])*x)
        return func
    
    def animate_move_to(entity: "Entity", end_pos: tuple[float, float]) -> Callable[[float], None]:
        """
        Creates a function to animate the movement of an entity to a specified end position, capturing the start position at the start of the animation.

        Args:
            entity (Entity): The entity to move.
            end_pos (tuple[float, float]): The target position of the entity.

        Returns:
            Callable[[float], None]: A function that updates the entity's position based on a progression value (0 to 1).
        """

        # Start position will be captured once when the animation starts
        start_pos = [None]

        def update_position(progression: float):
            if start_pos[0] is None:
                start_pos[0] = entity.rect.center  # Capture the start position at the start of the animation

            # Calculate new position based on progression
            new_x = start_pos[0][0] + (end_pos[0] - start_pos[0][0]) * progression
            new_y = start_pos[0][1] + (end_pos[1] - start_pos[0][1]) * progression

            # Set the entity's new position
            entity.set_center(new_x, new_y)

        return update_position

    @staticmethod
    def animate_alpha(entity:"Drawable", start : int, end:int)->Callable[[float],None]:
        """
        Creates a function to animate the alpha (transparency) of a drawable entity between a start and end value.

        Args:
            entity (Drawable): The entity to animate.
            start (int): The starting alpha value (0 to 255).
            end (int): The ending alpha value (0 to 255).

        Returns:
            Callable[[float], None]: A function that updates the entity's alpha based on a progression value (0 to 1).
        """
        def func(x):
            entity.set_alpha(int(pygame.math.clamp(start+(end-start)*x,0,255)))
        return func
    


    @staticmethod
    def random_color(min_value: int = 0, max_value: int = 255) -> tuple[int, int, int]:
        """
        Generates a random color as an RGB tuple.

        Args:
            min_value (int): Minimum value for each RGB component (inclusive). Defaults to 0.
            max_value (int): Maximum value for each RGB component (inclusive). Defaults to 255.

        Returns:
            tuple[int, int, int]: A tuple representing a random color in RGB format, with each component 
            between min_value and max_value.
        """
        return random.randint(min_value, max_value), random.randint(min_value, max_value), random.randint(min_value, max_value)

    @staticmethod
    def random_point_on_screen(margin: int = 0) -> tuple[int, int]:
        """
        Generates a random point on the screen, considering a margin from the edges.

        Args:
            margin (int): Margin from the screen edges, where the point won't be generated. 
                        If margin is less than 0 or greater than the screen resolution, returns (0, 0).

        Returns:
            tuple[int, int]: A tuple representing a random point (x, y) on the screen within the screen 
            resolution minus the margin.
        """
        if margin < 0 or margin > bf.const.RESOLUTION[0] or margin > bf.const.RESOLUTION[1]:
            return 0, 0
        return random.randint(margin, bf.const.RESOLUTION[0] - margin), random.randint(margin, bf.const.RESOLUTION[1] - margin)

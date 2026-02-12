import pygame
import batFramework as bf
import math
import random
from .enums import *
import re
from typing import Callable, TYPE_CHECKING
from functools import cache
if TYPE_CHECKING:
    from .drawable import Drawable
    from .entity import Entity
from pygame.math import Vector2


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
    def create_spotlight(inside_color, outside_color, radius, radius_stop=None, dest_surf=None,size=None,center:tuple|None=None,flags:int=pygame.SRCALPHA):
        """
        Creates a spotlight effect on a surface with a gradient from inside_color to outside_color.

        Args:
            inside_color (tuple[int, int, int]): RGB color at the center of the spotlight.
            outside_color (tuple[int, int, int]): RGB color at the outer edge of the spotlight.
            radius (int): Radius of the inner circle.
            radius_stop (int, optional): Radius where the spotlight ends. Defaults to the value of radius.
            dest_surf (pygame.Surface, optional): Surface to draw the spotlight on. Defaults to None.
            size (tuple[int, int], optional): Size of the surface if dest_surf is None. Defaults to a square based on radius_stop.
            center (tuple[int, int] | None, optional): Center coordinates of the spotlight. Defaults to the center of dest_surf.
            flags (int, optional): Pygame surface flags for creation. Defaults to pygame.SRCALPHA.

        Returns:
            pygame.Surface: The surface with the spotlight effect drawn on it.
        """

        if radius_stop is None:
            radius_stop = radius
        diameter = radius_stop * 2

        if dest_surf is None:
            if size is None:
                size = (diameter,diameter)
            dest_surf = pygame.Surface(size,flags)
        
        dest_surf.fill((0,0,0,0))

        if center is None:
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
                        If margin is less than 0 or greater than half the screen resolution, returns (0, 0).

        Returns:
            tuple[int, int]: A tuple representing a random point (x, y) on the screen within the screen 
            resolution minus the margin.
        """
        if margin < 0 or margin > bf.const.RESOLUTION[0]//2 or margin > bf.const.RESOLUTION[1]//2:
            return 0, 0
        return random.randint(margin, bf.const.RESOLUTION[0] - margin), random.randint(margin, bf.const.RESOLUTION[1] - margin)

    @staticmethod
    def distance_point(a:tuple[float,float],b:tuple[float,float]):
        return math.sqrt((a[0]-b[0]) ** 2 + (a[1]-b[1])**2)

    @staticmethod
    def rotate_point(point: Vector2, angle: float, center: Vector2) -> Vector2:
        """Rotate a point around a center by angle (in degrees)."""
        rad = math.radians(angle)
        translated = point - center
        rotated = Vector2(
            translated.x * math.cos(rad) - translated.y * math.sin(rad),
            translated.x * math.sin(rad) + translated.y * math.cos(rad)
        )
        return rotated + center

 
    def draw_triangle(surface:pygame.Surface, color, rect:pygame.FRect|pygame.Rect, direction:bf.enums.direction=bf.enums.direction.RIGHT,width:int=0):
        """
        Draw a filled triangle inside a rectangle on a Pygame surface, pointing in the specified direction.
        
        Args:
            surface: The Pygame surface to draw on.
            color: The color of the triangle (e.g., (255, 0, 0) for red).
            rect: A pygame.Rect object defining the rectangle's position and size.
            direction: A string ('up', 'down', 'left', 'right') indicating the triangle's orientation.
        """
        # Define the three vertices of the triangle based on direction
        rect = rect.copy()
        rect.inflate_ip(-1,-1)
        if direction == direction.UP:
            points = [
                (rect.left, rect.bottom),      # Bottom-left corner
                (rect.right, rect.bottom),     # Bottom-right corner
                (rect.centerx, rect.top)       # Top center (apex)
            ]
        elif direction == direction.DOWN:
            points = [
                (rect.left, rect.top),         # Top-left corner
                (rect.right, rect.top),        # Top-right corner
                (rect.centerx, rect.bottom)    # Bottom center (apex)
            ]
        elif direction == direction.LEFT:
            points = [
                (rect.right, rect.top),        # Top-right corner
                (rect.right, rect.bottom),     # Bottom-right corner
                (rect.left, rect.centery)      # Left center (apex)
            ]
        elif direction == direction.RIGHT:
            points = [
                (rect.left, rect.top),         # Top-left corner
                (rect.left, rect.bottom),      # Bottom-left corner
                (rect.right, rect.centery)     # Right center (apex)
            ]
        else:
            raise ValueError("Invalid direction")

        # Draw the filled triangle
        pygame.draw.polygon(surface, color, points,width=width)

    def draw_arc_by_points(surface, color, start_pos, end_pos, tightness=0.5, width=1, resolution=0.5,antialias:bool=False):
        """
        Draw a smooth circular arc connecting start_pos and end_pos.
        `tightness` controls curvature: 0 is straight line, 1 is semicircle, higher = more bulge.
        Negative tightness flips the bulge direction.

        Args:
            surface     - pygame Surface
            color       - RGB or RGBA
            start_pos   - (x, y)
            end_pos     - (x, y)
            tightness   - curvature control, 0 = straight, 1 = half circle
            width       - line width
            resolution  - approx pixels per segment
        Returns:
            pygame.Rect bounding the drawn arc
        """
        p0 = pygame.Vector2(start_pos)
        p1 = pygame.Vector2(end_pos)
        chord = p1 - p0
        if chord.length_squared() == 0:
            if antialias:
                return pygame.draw.aacircle(surface, color, p0, width // 2)
            return pygame.draw.circle(surface, color, p0, width // 2)

        # Midpoint and perpendicular
        mid = (p0 + p1) * 0.5
        perp = pygame.Vector2(-chord.y, chord.x).normalize()

        # Distance of center from midpoint, based on tightness
        h = chord.length() * tightness
        center = mid + perp * h

        # Radius and angles
        r = (p0 - center).length()
        ang0 = math.atan2(p0.y - center.y, p0.x - center.x)
        ang1 = math.atan2(p1.y - center.y, p1.x - center.x)

        # Normalize sweep direction based on sign of tightness
        sweep = ang1 - ang0
        if tightness > 0 and sweep < 0:
            sweep += 2 * math.pi
        elif tightness < 0 and sweep > 0:
            sweep -= 2 * math.pi

        # Number of points
        arc_len = abs(sweep * r)
        segs = max(2, int(arc_len / max(resolution, 1)))

        points = []
        for i in range(segs + 1):
            t = i / segs
            a = ang0 + sweep * t
            points.append((
                center.x + math.cos(a) * r,
                center.y + math.sin(a) * r
            ))
        if antialias:
            return pygame.draw.aalines(surface, color, False, points)
    
        return pygame.draw.lines(surface, color, False, points, width)

    @staticmethod
    def random_direction_vector():
        """
        Generate a random direction vector with unit length.
        Returns a normalized 2D vector pointing in a random direction. The vector
        is created by rotating a unit vector along the x-axis by a random angle
        between 0 and 360 degrees.
        Returns:
            pygame.Vector2: A normalized 2D vector with length 1.0 pointing in a random direction.
        """

        v = pygame.Vector2(1,0)
        v.rotate_ip(random.randint(0,360))
        v.normalize_ip()
        return v
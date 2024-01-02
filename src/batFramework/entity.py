from typing import Any, Self
import pygame
import batFramework as bf

class Entity:
    """
        Basic entity class
    """
    __instance_count = 0

    def __init__(
        self,
        size: None | tuple[int, int] = None,
        no_surface: bool = False,
        surface_flags: int = 0,
        convert_alpha: bool = False,
    ) -> None:
        self.convert_alpha = convert_alpha
        if size is None:
            size = (10, 10)
        if no_surface:
            self.surface = None
        else:
            self.surface = pygame.Surface(size, surface_flags)
            
        if convert_alpha and self.surface is not None:
            self.surface = self.surface.convert_alpha()
            self.surface.fill((0, 0, 0, 0))

        self.rect = pygame.FRect(0, 0, *size)
        self.tags: list[str] = []
        self.parent_scene: bf.Scene | None = None
        self.visible: bool = True
        self.debug_color: tuple = bf.color.DARK_RED
        self.render_order: int = 0
        self.rotation_origin = (0, 0)
        self.rotation: float = 0
        self._rotated_cache = (0,self.surface)
        self.uid: Any = Entity.__instance_count
        Entity.__instance_count += 1

    def set_rotation_origin(self, point: tuple) -> Self:
        self.rotation_origin = point
        return self

    def get_rotation_origin(self) -> tuple:
        return self.rotation_origin

    def rotate(self, value: float) -> Self:
        self.rotation = value
        self._rotated_cache = None
        return self

    def rotate_by(self, value: float) -> Self:
        self.rotation += value
        self._rotated_cache = None
        return self

    def set_render_order(self, render_order: int) -> Self:
        self.render_order = render_order
        return self

    def get_bounding_box(self):
        yield (self.rect, self.debug_color)

    def set_debug_color(self, color) -> Self:
        self.debug_color = color
        return self

    def set_visible(self, value: bool) -> Self:
        self.visible = value
        return self

    def set_parent_scene(self, scene) -> Self:
        self.parent_scene = scene
        return self

    def do_when_added(self):
        pass

    def do_when_removed(self):
        pass

    def set_position(self, x, y) -> Self:
        self.rect.topleft = (x, y)
        return self

    def get_position(self) -> tuple:
        return self.rect.topleft

    def get_center(self) -> tuple:
        return self.rect.center

    def set_x(self, x) -> Self:
        self.rect.x = x
        return self

    def set_y(self, y) -> Self:
        self.rect.y = y
        return self

    def set_center(self, x, y) -> Self:
        self.rect.center = (x, y)
        return self

    def set_uid(self, uid) -> Self:
        self.uid = uid
        return self

    def add_tags(self, *tags) -> Self:
        for tag in tags:
            if tag not in self.tags:
                self.tags.append(tag)
        self.tags.sort()
        return self

    def remove_tags(self, *tags):
        self.tags = [tag for tag in self.tags if tag not in tags]

    def has_tags(self, *tags) -> bool:
        return all(tag in self.tags for tag in tags)

    def get_tags(self) -> list[str]:
        return self.tags

    def process_event(self, event: pygame.Event) -> bool:
        """
        Returns bool : True if the method is blocking (no propagation to next children of the scene)
        """
        self.do_process_actions(event)
        res = self.do_handle_actions()
        res = res or self.do_handle_event(event)
        self.do_reset_actions()
        return res



    def do_process_actions(self, event: pygame.Event) -> None:
        """
            Process entity actions you may have set
        """

    def do_reset_actions(self) -> None:
        """
            Reset entity actions you may have set
        """

    def do_handle_actions(self) ->None:
        """
            Handle entity actions
        """

    def do_handle_event(self, event: pygame.Event) -> bool:
        """
            Handle specific
        """

        return False

    def update(self, dt: float):
        """
            Update method to be overriden by subclasses of widget
        """
        self.do_update(dt)

    def do_update(self, dt: float):
        """
            Update method to be overriden for specific behavior by the end user
        """

    def draw(self, camera: bf.Camera) -> int:
        """
            Draw the entity onto the camera with coordinate transposing
        """
        should_not_draw = not self.visible or not self.surface or not camera.intersects(self.rect)
        if should_not_draw:
            return 0
        if self.rotation == 0:
            camera.surface.blit(self.surface, camera.transpose(self.rect))
            return 1
        if self._rotated_cache is not None:
            camera.surface.blit(self._rotated_cache[1], camera.transpose(self.rect))
            return 1
            
        rotated = pygame.transform.rotate(self.surface,self.rotation)
        # if self.convert_alpha : rotated.convert_alpha()
        new_center = self.rect.move(self.rotation_origin[0],self.rotation_origin[1]).center
        tmp = rotated.get_rect(center = new_center)
        camera.surface.blit(rotated, camera.transpose(tmp))
        self._rotated_cache = (self.rotation,rotated)

        return 1

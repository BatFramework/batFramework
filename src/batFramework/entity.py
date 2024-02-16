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
        if size is None:
            if no_surface:
                size = (0,0)
            else:
                size = (10, 10)
        self.surface = None
        self.convert_alpha = convert_alpha
        self.blit_flags :int = 0#pygame.BLEND_PREMULTIPLIED if self.convert_alpha else 0
        self.rect = pygame.FRect(0, 0, *size)
        self.tags: list[str] = []
        self.parent_scene: bf.Scene | None = None
        self.visible: bool = True
        self.debug_color: tuple | str= "red"
        self.render_order: int = 0
        self.uid: int = Entity.__instance_count
        Entity.__instance_count += 1
        
        if not no_surface:
            self.surface = pygame.Surface(size, surface_flags).convert()
            if convert_alpha and self.surface is not None:
                self.surface = self.surface.convert_alpha()
                self.surface.fill((0, 0, 0, 0))


    def set_blit_flags(self,blit_flags:int)->Self:
        self.blit_flags = blit_flags
        return self

    def set_render_order(self, render_order: int) -> Self:
        self.render_order = render_order
        if self.parent_scene: self.parent_scene.sort_entities()
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

    def set_uid(self, uid:int) -> Self:
        self.uid = uid
        return self

    def get_uid(self)->int:
        return self.uid

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
        res = self.do_handle_event(event)
        return res

    def do_process_actions(self, event: pygame.Event) -> None:
        """
            Process entity actions you may have set
        """

    def do_reset_actions(self) -> None:
        """
            Reset entity actions you may have set
        """

    def do_handle_event(self, event: pygame.Event) -> bool:
        """
            Handle specific events with no action support
        """
        return False

    def update(self, dt: float)->None:
        """
            Update method to be overriden by subclasses of entity
        """
        self.do_update(dt)
        self.do_reset_actions()


    def do_update(self, dt: float)->None:
        """
            Update method to be overriden for specific behavior by the end user
        """

    def draw(self, camera: bf.Camera) -> int:
        """
            Draw the entity onto the camera with coordinate transposing
        """
        if not self.visible or not self.surface or not camera.intersects(self.rect):
            return 0
        camera.surface.blit(
            self.surface,
            camera.transpose(self.rect),
            special_flags = self.blit_flags)
        return 1

from __future__ import annotations
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .manager import Manager
    from .sceneManager import SceneManager
import pygame
import batFramework as bf


class Scene:
    def __init__(
        self,
        name: str,
        hud_convert_alpha: bool = True,
        world_convert_alpha: bool = False,
    ) -> None:
        """
        Initialize the Scene object.

        Args:
            name: Name of the scene.
            enable_alpha (bool, optional): Enable alpha channel for the scene surfaces. Defaults to True.
        """
        self.scene_index = 0
        self.name = name
        self.manager: Manager | None = None
        self.active = False
        self.visible = False
        self.world_entities: list[bf.Entity] = []
        self.hud_entities: list[bf.Entity] = []
        self.actions: bf.ActionContainer = bf.ActionContainer()
        self.early_actions: bf.ActionContainer = bf.ActionContainer()
        self.camera: bf.Camera = bf.Camera(convert_alpha=world_convert_alpha)
        self.hud_camera: bf.Camera = bf.Camera(convert_alpha=hud_convert_alpha)

        self.root: bf.Root = bf.Root(self.hud_camera)
        self.root.rect.center = self.hud_camera.get_center()
        self.add_hud_entity(self.root)

    def get_world_entity_count(self) -> int:
        return len(self.world_entities)

    def get_hud_entity_count(self) -> int:
        n = 0
        def adder(e):
            nonlocal n
            n += len(e.children)
        self.root.visit(adder)

        return len(self.hud_entities) + n 

    def set_scene_index(self, index: int):
        """Set the scene index."""
        self.scene_index = index

    def get_scene_index(self) -> int:
        """Get the scene index."""
        return self.scene_index

    def set_sharedVar(self, name: str, value: Any) -> bool:
        """
        Set a shared variable in the manager.

        Args:
            name: Name of the shared variable.
            value: Value to set.

        Returns:
            bool: True if setting was successful, False otherwise.
        """
        if not self.manager:
            return False
        return self.manager.set_sharedVar(name, value)

    def get_sharedVar(self, name: str, error_value=None) -> Any:
        """
        Get a shared variable from the manager.

        Args:
            name: Name of the shared variable.

        Returns:
            Any: Value of the shared variable.
        """
        if not self.manager:
            return error_value
        return self.manager.get_sharedVar(name, error_value)

    def do_when_added(self):
        pass

    def set_clear_color(self, color: pygame.Color | tuple):
        """Set the clear color for the camera."""
        self.camera.set_clear_color(color)

    def set_manager(self, manager_link: Manager):
        """Set the manager link for the scene."""
        self.manager = manager_link
        self.manager.update_scene_states()

    def set_visible(self, value: bool):
        """Set the visibility of the scene."""
        self.visible = value
        if self.manager:
            self.manager.update_scene_states()

    def set_active(self, value):
        """Set the activity of the scene."""
        self.active = value
        if self.manager:
            self.manager.update_scene_states()

    def is_active(self) -> bool:
        """Check if the scene is active."""
        return self.active

    def is_visible(self) -> bool:
        """Check if the scene is visible."""
        return self.visible

    def get_name(self) -> str:
        """Get the name of the scene."""
        return self.name

    def add_world_entity(self, *entity: bf.Entity):
        """Add world entities to the scene."""
        for e in entity:
            self.world_entities.append(e)
            e.parent_scene = self
            e.do_when_added()
        self.sort_entities()

    def remove_world_entity(self, *entity: bf.Entity):
        """Remove world entities from the scene."""
        for e in entity:
            if e not in self.world_entities:
                return False
            e.do_when_removed()
            e.parent_scene = None
            self.world_entities.remove(e)
            return True

    def add_hud_entity(self, *entity: bf.Entity):
        """Add HUD entities to the scene."""
        for e in entity:
            self.hud_entities.append(e)
            e.parent_scene = self
            e.do_when_added()
        self.sort_entities()
        return True

    def remove_hud_entity(self, *entity: bf.Entity):
        """Remove HUD entities from the scene."""
        for e in entity:
            if e in self.hud_entities:
                e.do_when_removed()
                e.parent_scene = None
                self.hud_entities.remove(e)

    def add_actions(self, *action):
        """Add actions to the scene."""
        self.actions.add_actions(*action)

    def add_early_actions(self, *action):
        """Add actions to the scene."""
        self.early_actions.add_actions(*action)

    def get_by_tags(self, *tags):
        """Get entities by their tags."""
        res = [
            entity
            for entity in self.world_entities + self.hud_entities
            if any(entity.has_tags(t) for t in tags)
        ]
        res.extend(list(self.root.get_by_tags(*tags)))
        return res

    def get_by_uid(self, uid) -> bf.Entity | None:
        """Get an entity by its unique identifier."""
        res = self._find_entity_by_uid(uid, self.world_entities + self.hud_entities)
        if res is None:
            res = self._recursive_search_by_uid(uid, self.root)
        return res

    def _find_entity_by_uid(self, uid, entities) -> bf.Entity | None:
        """Search for entity by uid in a list of entities."""
        for entity in entities:
            if entity.uid == uid:
                return entity
        return None

    def _recursive_search_by_uid(self, uid, widget) -> bf.Entity | None:
        """Recursively search for entity by uid in the widget's children."""
        if widget.uid == uid:
            return widget

        for child in widget.children:
            res = self._recursive_search_by_uid(uid, child)
            if res is not None:
                return res

        return None

    # propagates event to all entities
    def process_event(self, event: pygame.Event):
        """
        Propagates event while it is not consumed.
        In order : 
        -do_early_handle_event()
        -scene early_actions
        -propagate to scene entities (hud then world)
        -do_handle_event()
        -scene actions
        at each step, if the event is consumed the propagation stops
        """
        if event.consumed : return
        self.do_early_handle_event(event)
        if event.consumed : return
        self.early_actions.process_event(event)
        if event.consumed : return
        for entity in self.hud_entities + self.world_entities:
            entity.process_event(event)
            if event.consumed : return    
        self.do_handle_event(event)
        if event.consumed : return
        self.actions.process_event(event)

    # called before process event
    def do_early_handle_event(self, event: pygame.Event) :
        """Called early in event propagation"""
        pass

    def do_handle_event(self, event: pygame.Event):
        """called inside process_event but before resetting the scene's action container and propagating event to child entities of the scene"""
        pass

    def update(self, dt):
        """Update the scene. Do NOT override"""
        for entity in self.world_entities + self.hud_entities:
            entity.update(dt)
        self.do_update(dt)
        self.camera.update(dt)
        self.hud_camera.update(dt)
        self.actions.reset()
        self.early_actions.reset()

    def do_update(self, dt):
        """Specific update within the scene."""
        pass

    def debug_entity(self, entity: bf.Entity, camera: bf.Camera):
        def draw_rect(data):
            if data is None:
                return
            if isinstance(data, pygame.FRect) or isinstance(data, pygame.Rect):
                rect = data
                color = entity.debug_color
            else:
                rect = data[0]
                color = data[1]
            pygame.draw.rect(camera.surface, color, camera.world_to_screen(rect), 1)

        [draw_rect(data) for data in entity.get_debug_outlines()]

    def sort_entities(self) -> None:
        """Sort entities within the scene based on their rendering order."""
        self.world_entities.sort(key=lambda e: e.render_order)
        self.hud_entities.sort(key=lambda e: e.render_order)

    def _draw_camera(self, camera: bf.Camera, entity_list: list[bf.Entity]) ->None:
        _ = [entity.draw(camera) for entity in entity_list]
        debugMode = self.manager.debug_mode
        # Draw outlines for world entities if required
        if debugMode == bf.debugMode.OUTLINES:
            [self.debug_entity(e, camera) for e in entity_list]


    def draw(self, surface: pygame.Surface):

        self.camera.clear()
        self.hud_camera.clear()

        # Draw all world entities
        self._draw_camera(self.camera, self.world_entities)
        # Draw all HUD entities
        self._draw_camera(self.hud_camera, self.hud_entities)

        self.do_early_draw(surface)
        self.camera.draw(surface)
        self.do_post_world_draw(surface)
        self.hud_camera.draw(surface)
        self.do_final_draw(surface)

    def do_early_draw(self, surface: pygame.Surface):
        pass

    def do_post_world_draw(self, surface: pygame.Surface):
        pass

    def do_final_draw(self, surface: pygame.Surface):
        pass

    def on_enter(self):
        self.set_active(True)
        self.set_visible(True)
        self.root.clear_hovered()
        # self.root.clear_focused()
        self.root.build()
        self.do_on_enter()
        # self.root.visit(lambda e : e.resolve_constraints())

    def on_exit(self):
        self.root.clear_hovered()
        # self.root.clear_focused()
        self.set_active(False)
        self.set_visible(False)
        self.actions.hard_reset()
        self.early_actions.hard_reset()
        self.do_on_exit()

    def do_on_enter(self) -> None:
        pass

    def do_on_exit(self) -> None:
        pass

    def do_on_enter_early(self) -> None:
        pass

    def do_on_exit_early(self) -> None:
        pass

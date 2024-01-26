from __future__ import annotations
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .manager import Manager
    from .sceneManager import SceneManager
import pygame
import batFramework as bf


class Scene:
    def __init__(self, name: str, enable_alpha: bool = True) -> None:
        """
        Initialize the Scene object.

        Args:
            name: Name of the scene.
            enable_alpha (bool, optional): Enable alpha channel for the scene surfaces. Defaults to True.
        """
        self.scene_index = 0
        self._name = name
        self.manager: Manager | None = None
        self._active = False
        self._visible = False
        self._world_entities: list[bf.Entity] = []
        self._hud_entities: list[bf.Entity] = []
        self.actions: bf.ActionContainer = bf.ActionContainer()
        self.early_actions: bf.ActionContainer = bf.ActionContainer()
        self.camera: bf.Camera = bf.Camera(convert_alpha=enable_alpha)
        self.hud_camera: bf.Camera = bf.Camera(convert_alpha=True)

        self.root: bf.Root = bf.Root(self.hud_camera)
        self.root.set_center(*self.hud_camera.get_center())
        self.add_hud_entity(self.root)
        self.blit_calls = 0


    def get_world_entity_count(self)->int:
        return len(self._world_entities)


    def get_hud_entity_count(self)->int:
        return len(self._hud_entities) + self.root.count_children_recursive() -1


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

    def get_sharedVar(self, name: str,error_value=None) -> Any:
        """
        Get a shared variable from the manager.

        Args:
            name: Name of the shared variable.

        Returns:
            Any: Value of the shared variable.
        """
        if not self.manager:
            return error_value
        return self.manager.get_sharedVar(name,error_value)

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
        self._visible = value
        if self.manager:
            self.manager.update_scene_states()

    def set_active(self, value):
        """Set the activity of the scene."""
        self._active = value
        if self.manager:
            self.manager.update_scene_states()

    def is_active(self) -> bool:
        """Check if the scene is active."""
        return self._active

    def is_visible(self) -> bool:
        """Check if the scene is visible."""
        return self._visible

    def get_name(self) -> str:
        """Get the name of the scene."""
        return self._name

    def add_world_entity(self, *entity: bf.Entity):
        """Add world entities to the scene."""
        for e in entity:
            self._world_entities.append(e)
            e.parent_scene = self
            e.do_when_added()
        self.sort_entities()

    def remove_world_entity(self, *entity: bf.Entity):
        """Remove world entities from the scene."""
        for e in entity:
            if e not in self._world_entities:
                return False
            e.do_when_removed()
            e.parent_scene = None
            self._world_entities.remove(e)
            return True

    def add_hud_entity(self, *entity: bf.Entity):
        """Add HUD entities to the scene."""
        for e in entity:
            self._hud_entities.append(e)
            e.parent_scene = self
            e.do_when_added()
        self.sort_entities()
        return True

    def remove_hud_entity(self, *entity: bf.Entity):
        """Remove HUD entities from the scene."""
        for e in entity:
            if e in self._hud_entities:
                e.do_when_removed()
                e.parent_scene = None
                self._hud_entities.remove(e)

    def add_action(self, *action):
        """Add actions to the scene."""
        self.actions.add_action(*action)

    def add_early_action(self, *action):
        """Add actions to the scene."""
        self.early_actions.add_action(*action)

    def get_by_tags(self, *tags):
        """Get entities by their tags."""
        res = [
            entity
            for entity in self._world_entities + self._hud_entities
            if any(entity.has_tags(t) for t in tags)
        ]
        res.extend(list(self.root.get_by_tags(*tags)))
        return res

    def get_by_uid(self, uid) -> bf.Entity | None:
        """Get an entity by its unique identifier."""
        res = self._find_entity_by_uid(uid, self._world_entities + self._hud_entities)
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

    # called before process event
    def do_early_process_event(self, event: pygame.Event) -> bool:
        """return True if stop event propagation in child entities and scene's action container"""
        return False

    # propagates event to all entities
    def process_event(self, event: pygame.Event):
        """
        Propagates event to child events. Calls early process event first, if returns False then stops. Processes scene's action_container, then custom do_handle_event function.
        Finally resets the action_container, and propagates to all child entities. if any of them returns True, the propagation is stopped.
        """

        if self.do_early_process_event(event):
            return
        self.early_actions.process_event(event)
        self.do_handle_actions()
        self.do_handle_event(event)
        for entity in self._hud_entities + self._world_entities:
            if entity.process_event(event):
                return
        self.actions.process_event(event)


    def do_handle_actions(self) -> None:
        """Handle actions within the scene."""
        pass

    def do_handle_event(self, event: pygame.Event):
        """called inside process_event but before resetting the scene's action container and propagating event to child entities of the scene"""
        pass

    def update(self, dt):
        """Update the scene. Do NOT override"""
        for entity in self._world_entities + self._hud_entities:
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
        if not entity.visible:
            return
        # bounding_box = entity.get_bounding_box()
        # if bounding_box is None : return
        for data in entity.get_bounding_box():
            if data is None : return
            if isinstance(data, pygame.FRect):
                rect = data
                color = entity.debug_color
            else:
                rect = data[0]
                color = data[1]

            pygame.draw.rect(camera.surface, color, camera.transpose(rect), 1)

    def sort_entities(self) -> None:
        """Sort entities within the scene based on their rendering order."""
        self._world_entities.sort(key=lambda e: e.render_order)
        self._hud_entities.sort(key=lambda e: e.render_order)

    def draw(self, surface: pygame.Surface):
        total_blit_calls = 0
        if not self.manager : return
        self.camera.clear()
        self.hud_camera.clear()

        show_outlines = self.manager._debugging in [2, 3]
        show_only_visible_outlines = self.manager._debugging != 3


        #   draw all world entities
        total_blit_calls += sum(entity.draw(self.camera) for entity in self._world_entities)

        #   
        if show_outlines:
            [self.debug_entity(entity, self.camera) for entity\
            in self._world_entities if not  show_only_visible_outlines\
            or (show_only_visible_outlines and entity.visible)]

        total_blit_calls += sum(entity.draw(self.hud_camera) for entity in self._hud_entities)

        if show_outlines:
            [self.debug_entity(entity, self.hud_camera) for entity\
            in self._hud_entities if  not show_only_visible_outlines\
            or (show_only_visible_outlines and entity.visible)]

        self.do_early_draw(surface)
        self.camera.draw(surface)
        self.hud_camera.draw(surface)
        self.do_final_draw(surface)
        self.blit_calls = total_blit_calls

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
        self.root.clear_focused()
        self.root.build()
        self.do_on_enter()

    def on_exit(self):
        self.root.clear_hovered()
        self.root.clear_focused()
        self.set_active(False)
        self.set_visible(False)
        self.actions.hard_reset()
        self.early_actions.hard_reset()
        self.do_on_exit()

    def do_on_enter(self)->None:
        pass

    def do_on_exit(self)->None:
        pass

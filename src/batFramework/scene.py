from __future__ import annotations
import re
from collections import OrderedDict
import itertools

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
        bf.TimeManager().add_register(self.name,False)
        self.manager: Manager | None = None
        self.active = False
        self.visible = False
        self.world_entities: OrderedDict[bf.Entity, None] = OrderedDict()
        self.hud_entities: OrderedDict[bf.Entity, None] = OrderedDict()
        self.actions: bf.ActionContainer = bf.ActionContainer()
        self.early_actions: bf.ActionContainer = bf.ActionContainer()
        self.camera: bf.Camera = bf.Camera(convert_alpha=world_convert_alpha)
        self.hud_camera: bf.Camera = bf.Camera(convert_alpha=hud_convert_alpha)
        self.should_sort :bool = True
        self.root: bf.Root = bf.Root(self.hud_camera)
        self.root.rect.center = self.hud_camera.get_center()
        self.add_hud_entity(self.root)
        self.entities_to_remove = []
        self.entities_to_add = []


    def __str__(self)->str:
        return f"Scene({self.name})"

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

    def add_world_entity(self, *entities: bf.Entity):
        """Add world entities to the scene."""
        change = False
        for e in entities:
            if e not in self.world_entities and e not in self.entities_to_add:
                change = True
                # self.world_entities[e] = None
                self.entities_to_add.append(e)
                e.set_parent_scene(self)
        # self.sort_entities()
        return change

    # Updated remove_world_entity method to add entities to the removal list
    def remove_world_entity(self, *entities: bf.Entity):
        """Mark world entities for removal from the scene."""
        change = False
        for e in entities:
            if e in self.world_entities:
                change = True
                self.entities_to_remove.append(e)
                e.set_parent_scene(None)
        return change

    def add_hud_entity(self, *entities: bf.Entity):
        """Add HUD entities to the scene."""
        for e in entities:
            if e not in self.hud_entities:
                self.hud_entities[e] = None
                e.set_parent_scene(self)
        self.sort_entities()
        return True

    def remove_hud_entity(self, *entities: bf.Entity):
        """Remove HUD entities from the scene."""
        for e in entities:
            if e in self.hud_entities:
                e.set_parent_scene(None)
                self.hud_entities.pop(e)

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
            for entity in itertools.chain(
                self.world_entities.keys(), self.hud_entities.keys()
            )
            if any(entity.has_tags(t) for t in tags)
        ]
        res.extend(list(self.root.get_by_tags(*tags)))
        return res

    def get_by_uid(self, uid) -> bf.Entity | None:
        """Get an entity by its unique identifier."""
        res = self._find_entity_by_uid(
            uid, itertools.chain(self.world_entities.keys(), self.hud_entities.keys())
        )
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
        if event.consumed:
            return
        self.do_early_handle_event(event)
        if event.consumed:
            return
        self.early_actions.process_event(event)
        if event.consumed:
            return
        for entity in itertools.chain(
            self.hud_entities.keys(), self.world_entities.keys()
        ):
            entity.process_event(event)
            if event.consumed:
                return
        self.do_handle_event(event)
        if event.consumed:
            return
        self.actions.process_event(event)

    # called before process event
    def do_early_handle_event(self, event: pygame.Event):
        """Called early in event propagation"""
        pass

    def do_handle_event(self, event: pygame.Event):
        """called inside process_event but before resetting the scene's action container and propagating event to child entities of the scene"""
        pass

    def update(self, dt):
        """Update the scene. Do NOT override"""
        if self.should_sort:
            self._sort_entities_internal()

        for entity in itertools.chain(
            self.hud_entities.keys(), self.world_entities.keys()
        ):
            entity.update(dt)
        
        self.do_update(dt)
        self.camera.update(dt)
        self.hud_camera.update(dt)
        self.actions.reset()
        self.early_actions.reset()

        if self.entities_to_add:
            for e in self.entities_to_add:
                self.world_entities[e] = None
            self.entities_to_add.clear()

        # Remove marked entities after updating
        if self.entities_to_remove:
            for e in self.entities_to_remove:
                self.world_entities.pop(e, None)
            self.entities_to_remove.clear()

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
        self.should_sort = True

    def _sort_entities_internal(self):
        """Sort entities within the scene based on their rendering order."""
        self.world_entities = OrderedDict(
            sorted(self.world_entities.items(), key=lambda e: e[0].render_order)
        )
        self.hud_entities = OrderedDict(
            sorted(self.hud_entities.items(), key=lambda e: e[0].render_order)
        )
        self.should_sort = False

    def draw(self, surface: pygame.Surface):
        self.camera.clear()
        self.hud_camera.clear()

        # Draw all world entities
        self._draw_camera(self.camera, self.world_entities.keys())
        # Draw all HUD entities
        self._draw_camera(self.hud_camera, self.hud_entities.keys())

        self.do_early_draw(surface)
        self.camera.draw(surface)
        self.do_post_world_draw(surface)
        self.hud_camera.draw(surface)
        self.do_final_draw(surface)

    def _draw_camera(self, camera: bf.Camera, entity_list):
        _ = [entity.draw(camera) for entity in entity_list]
        debugMode = bf.ResourceManager().get_sharedVar("debug_mode")
        # Draw outlines for world entities if required
        if debugMode == bf.debugMode.OUTLINES:
            [self.debug_entity(e, camera) for e in entity_list]

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
        self.root.build()
        bf.TimeManager().activate_register(self.name)
        self.do_on_enter()

    def on_exit(self):
        self.root.clear_hovered()
        self.set_active(False)
        self.set_visible(False)
        self.actions.hard_reset()
        self.early_actions.hard_reset()
        bf.TimeManager().deactivate_register(self.name)
        self.do_on_exit()

    def do_on_enter(self) -> None:
        pass

    def do_on_exit(self) -> None:
        pass

    def do_on_enter_early(self) -> None:
        pass

    def do_on_exit_early(self) -> None:
        pass

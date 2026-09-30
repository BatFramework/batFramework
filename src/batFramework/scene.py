from __future__ import annotations
from typing import TYPE_CHECKING, Self

from batFramework.drawable import Drawable
from batFramework.entity import Entity

if TYPE_CHECKING:
    from .manager import Manager

import pygame
import math
import logging
import batFramework as bf

logger = logging.getLogger(__name__)


class Scene:
    def __init__(self, name: str, convert_alpha: bool = False) -> None:
        """
        Base Scene object.

        Entities are drawn layer by layer (see bf.Layer), each layer with its own camera,
        then by draw_order within a layer:
        - Layer.WORLD: self.camera
        - Layer.HUD: self.hud_camera (screen space, never zoomed or moved, used by the gui)
        More layers can be added with add_layer.

        Args:
            name: Name of the scene.
        """
        bf.TimeManager().add_register(name, False)
        self.scene_index = 0
        self.name = name
        self.manager: Manager | None = None
        self.active = False
        self.visible = False
        self.actions: bf.ActionContainer = bf.ActionContainer()
        self.early_actions: bf.ActionContainer = bf.ActionContainer()

        self._should_reorder_entities:bool = False
        self.entities: list[Entity] = []
        self.entities_to_add: set[Entity] = set()  # entities to add to the scene, (1 frame delay after calling add)
        self.entities_to_remove: set[Entity] = set()
        self.camera = bf.Camera(convert_alpha=convert_alpha)
        # transparent, drawn over the world
        self.hud_camera = bf.Camera(convert_alpha=True)

        # layers in draw order, and the camera of each
        self._layers: list[str] = [bf.Layer.WORLD, bf.Layer.HUD]
        self._layer_cameras: dict[str, bf.Camera] = {
            bf.Layer.WORLD: self.camera,
            bf.Layer.HUD: self.hud_camera,
        }
        self._layer_indices: dict[str, int] = {}
        self._warned_layers: set[str] = set()
        self._update_layer_indices()

        self.root: bf.gui.Root = bf.gui.Root(self.hud_camera)
        self.root.rect.topleft = self.hud_camera.get_position()
        self.add(self.root)

    def set_clear_color(self, color):
        """
        Sets the clear color of the entire scene.
        This color will fill the scene before all layers are drawn.
        Results will not show if a layer has an opaque fill color on top.
        Set to None to skip.
        """
        self.camera.clear_color = color

    # ------------------------------------------------------------------
    # Layers
    # ------------------------------------------------------------------

    def _update_layer_indices(self) -> None:
        self._layer_indices = {layer: i for i, layer in enumerate(self._layers)}
        self.request_draw_order_update()

    def add_layer(
        self,
        layer: str,
        camera: bf.Camera | None = None,
        before: str | None = None,
        after: str | None = None,
    ) -> Self:
        """
        Add a layer drawn with camera (a new transparent camera if None).
        It is drawn on top of every layer unless before or after is given.
        """
        if layer in self._layer_cameras:
            logger.warning(f"Layer '{layer}' already exists in {self}")
            return self
        if before is not None and after is not None:
            raise ValueError("Use either before or after, not both")
        index = len(self._layers)
        anchor = before if before is not None else after
        if anchor is not None:
            if anchor not in self._layer_indices:
                raise ValueError(f"Layer '{anchor}' does not exist in {self}")
            index = self._layer_indices[anchor] + (1 if after is not None else 0)
        self._layers.insert(index, layer)
        self._layer_cameras[layer] = (
            camera if camera is not None else bf.Camera(convert_alpha=True)
        )
        self._warned_layers.discard(layer)
        self._update_layer_indices()
        return self

    def remove_layer(self, layer: str) -> Self:
        """Entities left on a removed layer are drawn on the world layer"""
        if layer == bf.Layer.WORLD:
            raise ValueError("The world layer can't be removed")
        if layer in self._layer_cameras:
            self._layers.remove(layer)
            del self._layer_cameras[layer]
            self._update_layer_indices()
        return self

    def set_layer_camera(self, layer: str, camera: bf.Camera) -> Self:
        if layer not in self._layer_cameras:
            raise ValueError(f"Layer '{layer}' does not exist in {self}")
        self._layer_cameras[layer] = camera
        if layer == bf.Layer.WORLD:
            self.camera = camera
        elif layer == bf.Layer.HUD:
            self.hud_camera = camera
        return self

    def get_layers(self) -> list[str]:
        """Layers in draw order"""
        return list(self._layers)

    def get_camera(self, layer: str = bf.Layer.WORLD) -> bf.Camera:
        """Camera used to draw the layer (the world camera for unknown layers)"""
        camera = self._layer_cameras.get(layer)
        if camera is None:
            if layer not in self._warned_layers:
                self._warned_layers.add(layer)
                logger.warning(
                    f"Layer '{layer}' does not exist in {self}, drawing it on the world layer"
                )
            return self.camera
        return camera

    def get_cameras(self) -> list[bf.Camera]:
        """All distinct cameras of the scene, in layer order"""
        cameras = []
        for layer in self._layers:
            camera = self._layer_cameras[layer]
            if camera not in cameras:
                cameras.append(camera)
        return cameras

    def get_mouse_pos(self, layer: str = bf.Layer.WORLD) -> tuple:
        """Mouse position in the coordinates of the layer's camera"""
        return self.get_camera(layer).get_mouse_pos()

    def get_clear_color(self) -> pygame.typing.ColorLike:
        return self.camera.clear_color
    
    def get_by_tags(self, *tags) -> list[Entity]:
        return [v for v in self.entities if v.has_tags(*tags)]

    def get_by_uid(self, uid: int) -> Entity | None:
        for entity in self.entities:
            if entity.uid == uid:
                return entity
        return None

    def add(self, *entities: Entity):
        for e in entities:
            if isinstance(e, Drawable) and e.parent_group is not None:
                logger.warning(f"{e} is in {e.parent_group}, remove it from the group before adding it to a scene")
                continue
            if e.parent_scene != self and e not in self.entities_to_add:
                self.entities_to_add.add(e)

    def remove(self, *entities: Entity):
        for e in entities:
            if isinstance(e, Drawable) and e.parent_group is not None:
                # entities in a group are owned by the group
                e.parent_group.remove(e)
                continue
            if e.parent_scene == self and e not in self.entities_to_remove:
                self.entities_to_remove.add(e)

    def __str__(self) -> str:
        return f"Scene({self.name})"

    def set_scene_index(self, index: int):
        """Set the scene index."""
        self.scene_index = index

    def get_scene_index(self) -> int:
        """Get the scene index."""
        return self.scene_index

    def when_added(self):
        self.flush_entity_changes()
        self.do_when_added()

    def do_when_added(self):
        pass

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

    def get_all_by_tags(self, *tags) -> list[Entity]:
        """Get entities by their tags."""
        return [e for e in self.entities if e.has_tags(*tags)]

    def get_by_tags(self, *tags) -> Entity | None:
        """Get the first entity that matches the given tags."""
        for e in self.entities:
            if e.has_tags(*tags):
                return e
        return None

    def get_by_uid(self, uid) -> bf.Entity | None:
        """Get an entity by its unique identifier."""
        for e in self.entities:
            if e.uid == uid:
                return e
        return None

    def add_actions(self, *action):
        """Add actions to the scene."""
        self.actions.add_actions(*action)

    def add_early_actions(self, *action):
        """Add actions to the scene."""
        self.early_actions.add_actions(*action)

    def process_event(self, event: pygame.Event):
        """
        Propagates event while it is not consumed.
        In order : do_early_handle_event
        -> scene early_actions
        -> propagate to all entities 
        -> handle_event
        -> scene actions.
        at each step, if the event is consumed the propagation stops
        """
        self.do_early_handle_event(event)
        if event.consumed:
            return
        self.early_actions.process_event(event)
        if event.consumed:
            return

        if self.manager.current_transition and event.type in bf.enums.playerInput:
            return

        if event.type == pygame.VIDEORESIZE and not pygame.SCALED & bf.const.FLAGS:
            for camera in self.get_cameras():
                if camera.fullscreen:
                    camera.set_size(bf.const.RESOLUTION)

        for e in reversed(self.entities):
            e.process_event(event)
            if event.consumed:
                return

        self.handle_event(event)

        if event.consumed:
            return
        self.actions.process_event(event)

    # called before process event
    def do_early_handle_event(self, event: pygame.Event):
        """Called early in event propagation"""
        pass

    def handle_event(self, event: pygame.Event):
        """called inside process_event but before resetting the scene's action container and propagating event to scene entities"""
        pass

    def update(self, dt):
        # Update all entities
        for e in reversed(self.entities):
            e.update(dt)

        self.flush_entity_changes()

        self.do_update(dt)
        # Update the cameras
        for camera in self.get_cameras():
            camera.update(dt)
        self.actions.reset()
        self.early_actions.reset()        

    def do_update(self, dt):
        """Specific update within the scene."""
        pass

    def flush_entity_changes(self):
        """
        Synchronizes entity changes by removing entities marked for removal,
        adding new entities, and updating the draw order if necessary.
        """
        # Remove entities marked for removal
        for e in self.entities_to_remove:
            e.set_parent_scene(None)
            
        self.entities = [e for e in self.entities if e not in self.entities_to_remove]
        self.entities_to_remove.clear()

        # Add new entities
        reorder = self._should_reorder_entities
        for e in self.entities_to_add:
            self.entities.append(e)
            e.set_parent_scene(self)
            if not reorder and isinstance(e, Drawable):
                reorder = True
        self.entities_to_add.clear()

        # Reorder draw order if necessary
        if reorder:
            self._update_draw_order()
        self._should_reorder_entities = False

    def draw(self, surface: pygame.Surface):
        """
        Draws entities layer by layer, each run of entities sharing a camera into that camera,
        which is then drawn onto surface before switching to the next camera.
        The world camera always comes first, so its clear color is the scene background.
        """
        get_camera = self.get_camera
        camera = self.camera
        camera.clear()
        run: list[Drawable] = []  # entities drawn with the current camera (for debug outlines)
        for e in self.entities:
            if not isinstance(e, Drawable):
                continue
            e_camera = get_camera(e.draw_layer)
            if e_camera is not camera:
                self._present_camera(camera, run, surface)
                camera = e_camera
                camera.clear()
                run = []
            e.draw(camera)
            run.append(e)
        self._present_camera(camera, run, surface)

    def _present_camera(
        self, camera: bf.Camera, entities: list[Drawable], surface: pygame.Surface
    ) -> None:
        if bf.Context.debug_mode == bf.debugMode.OUTLINES:
            for e in entities:
                self.debug_entity(e, camera)
        camera.draw(surface)

    def _update_draw_order(self):
        # unknown layers sort with the world layer (index 0), where they are drawn
        layer_index = self._layer_indices.get
        self.entities.sort(
            key=lambda o: (layer_index(o.draw_layer, 0), o.draw_order)
            if isinstance(o, Drawable)
            else (0, 0)
        )

    def request_draw_order_update(self):
        self._should_reorder_entities = True

    def debug_entity(self, entity: Entity, camera: bf.Camera | None = None):
        if camera is None:
            camera = self.camera

        def draw_rect(data):
            if data is None:
                return
            if isinstance(data, pygame.FRect) or isinstance(data, pygame.Rect):
                rect = data
                color = entity.debug_color
            else:
                rect = data[0]
                color = data[1]
            if camera.intersects(rect):
                line_width = (
                    1
                    if camera.zoom_factor >= 1
                    else int(-math.log2(camera.zoom_factor)) + 2 # increase line width as zoom decreases to maintain visibility
                )
                pygame.draw.rect(
                    camera.surface,
                    color,
                    camera.world_to_screen(rect),
                    line_width,
                )

        for data in entity.get_debug_outlines():
            draw_rect(data)

    def on_enter(self):
        self.root.clear_hovered()
        self.root.update_tree()
        bf.TimeManager().activate_register(self.name)
        self.do_on_enter()

    def on_exit(self):
        self.root.clear_hovered()
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

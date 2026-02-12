from __future__ import annotations
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from .manager import Manager
    from .sceneManager import SceneManager

import pygame
import itertools
import batFramework as bf
from .sceneLayer import SceneLayer

class BaseScene:
    def __init__(self,name: str) -> None:
        """
        Base Scene object.
        Empty scene with no layers or gui setup
        Args:
            name: Name of the scene.
        """
        bf.TimeManager().add_register(name,False)
        self.scene_index = 0
        self.name = name
        self.manager: Manager | None = None
        self.active = False
        self.visible = False
        self.clear_color = bf.color.BLACK
        self.actions: bf.ActionContainer = bf.ActionContainer()
        self.early_actions: bf.ActionContainer = bf.ActionContainer()
        self.scene_layers : list[SceneLayer] = []
    
    def set_clear_color(self,color):
        """
        Sets the clear color of the entire scene.
        This color will fill the scene before all layers are drawn.
        Results will not show if a layer has an opaque fill color on top.
        Set to None to skip.
        """
        self.clear_color = color

    def get_mouse_pos(self,reference_layer:str|None=None)->tuple|None:
        if reference_layer is None:
            return pygame.mouse.get_pos()
        layer = self.get_layer(reference_layer)
        if not layer:
            return None
        return layer.get_mouse_pos()

    def get_clear_color(self)->pygame.typing.ColorLike:
        return self.clear_color

    def add_layer(self,layer:SceneLayer,index:int=0):
        layer.set_scene(self)
        self.scene_layers.insert(index,layer)

    def remove_layer(self,index=0):
        self.scene_layers.pop(index)

    def set_layer(self,layername,layer:SceneLayer):
        for i,l in enumerate(self.scene_layers[::]):
            if l.name == layername:
                self.scene_layers[i] = layer
                layer.set_scene(self)

    def set_layer_index(self,layername:str,index:int=-1):
        index = min(index,len(self.scene_layers)-1)
        layer = self.get_layer(layername)
        if layer is None : return
        self.scene_layers.remove(layer)
        self.scene_layers.insert(index,layer)

    def get_layer(self,name:str)->bf.SceneLayer:
        for s in self.scene_layers:
            if s.name == name:
                return s
        return None

    def add(self,layer:str,*entities):
        l = self.get_layer(layer)
        if l is None : return 
        l.add(*entities)

    def remove(self,layer:str,*entities):
        l = self.get_layer(layer)
        if l is None : return
        l.remove(*entities)

    def __str__(self)->str:
        return f"Scene({self.name})"

    def set_scene_index(self, index: int):
        """Set the scene index."""
        self.scene_index = index

    def get_scene_index(self) -> int:
        """Get the scene index."""
        return self.scene_index

    def when_added(self):
        for s in self.scene_layers:
            s.flush_entity_changes()
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

    def get_by_tags(self, *tags):
        """Get entities by their tags."""
        return itertools.chain.from_iterable(l.get_by_tags(*tags) for l in self.scene_layers)

    def get_by_uid(self, uid) -> bf.Entity | None:
        """Get an entity by its unique identifier."""
        for l in self.scene_layers:
            r = l.get_by_uid(uid)
            if r is not None:
                return r
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
        -> propagate to all layers
        -> handle_event
        -> scene actions.
        at each step, if the event is consumed the propagation stops
        """
        self.do_early_handle_event(event)
        if event.consumed: return
        self.early_actions.process_event(event)
        if event.consumed: return

        if self.manager.current_transition and event.type in bf.enums.playerInput:
            return 
        
        for l in self.scene_layers:
            l.process_event(event)
            if event.consumed : return
            
        self.handle_event(event)

        if event.consumed:return
        self.actions.process_event(event)

    # called before process event
    def do_early_handle_event(self, event: pygame.Event):
        """Called early in event propagation"""
        pass

    def handle_event(self, event: pygame.Event):
        """called inside process_event but before resetting the scene's action container and propagating event to scene layers"""
        pass

    def update(self, dt):
        """Update the scene. Do NOT override"""

        #update all scene layers
        for l in self.scene_layers:
            l.update(dt)
        self.do_update(dt)
        self.actions.reset()
        self.early_actions.reset()


    def do_update(self, dt):
        """Specific update within the scene."""
        pass


    def draw(self, surface: pygame.Surface):
        if self.clear_color is not None:
            surface.fill(self.clear_color)
        self.do_early_draw(surface)

        # Draw all layers back to front
        for i,l in enumerate(reversed(self.scene_layers)):
            #blit all layers onto surface
            l.draw(surface)
            if i < len(self.scene_layers)-1:
                self.do_between_layer_draw(surface,l)
        self.do_final_draw(surface)


    def do_early_draw(self, surface: pygame.Surface):
        """Called before any layer draw"""
        pass

    def do_between_layer_draw(self, surface: pygame.Surface,layer:SceneLayer):
        """Called after drawing the argument layer (except the last layer)"""
        pass

    def do_final_draw(self, surface: pygame.Surface):
        "Called after all layers"
        pass

    def on_enter(self):
        self.set_active(True)
        self.set_visible(True)
        bf.TimeManager().activate_register(self.name)
        self.do_on_enter()

    def on_exit(self):
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

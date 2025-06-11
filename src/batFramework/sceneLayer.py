from __future__ import annotations
import batFramework as bf
import pygame
from .entity import Entity
from .drawable import Drawable

from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from .baseScene import BaseScene 

class SceneLayer:
    """
    A scene layer is a 'dimension' bound to a scene
    Each layer contains its own entities and camera
    One common use would be to separate GUI and game into two separate layers
    """
    def __init__(self,name:str,convert_alpha:bool = False):
        self.scene = None
        self.name = name
        self.entities : dict[int,Entity] = {}
        self.entities_to_add : set[Entity]= set()
        self.entities_to_remove : set[Entity]= set()
        self.draw_order : list[int] = []
        self.camera = bf.Camera(convert_alpha=convert_alpha)

    def set_clear_color(self,color):
        self.camera.set_clear_color(color)

    def set_scene(self, scene:BaseScene):
        self.scene = scene

    def add(self,*entities:Entity):
        for e in entities:
            if e.uid not in self.entities and e not in self.entities_to_add:
                self.entities_to_add.add(e)


    def get_by_tags(self,*tags)->list[Entity]:
        return [v for v in self.entities.values() if v.has_tags(*tags) ]

    def get_by_uid(self,uid:int)->Entity|None:
        return self.entities.get(uid,None)

    def remove(self,*entities:Entity):
        for e in entities:
            if e.uid in self.entities and e not in self.entities_to_remove:
                self.entities_to_remove.add(e)

    def process_event(self,event:pygame.Event):
        if event.type == pygame.VIDEORESIZE and not pygame.SCALED & bf.const.FLAGS:
            self.camera.set_size(bf.const.RESOLUTION)

        for e in self.entities.values():
            e.process_event(event)
            if event.consumed : return

    def update(self, dt):
        # Update all entities
        for e in self.entities.values():
            e.update(dt)

        self.flush_entity_changes()

        # Update the camera
        self.camera.update(dt)

    def flush_entity_changes(self):
        """
        Synchronizes entity changes by removing entities marked for removal,
        adding new entities, and updating the draw order if necessary.
        """


        # Remove entities marked for removal
        for e in self.entities_to_remove:
            if e.uid in self.entities.keys():
                e.set_parent_scene(None)
                self.entities.pop(e.uid)
        self.entities_to_remove.clear()

        # Add new entities
        reorder = False
        for e in self.entities_to_add:
            self.entities[e.uid] = e
            e.set_parent_layer(self)
            e.set_parent_scene(self.scene)
            if not reorder and isinstance(e, Drawable):
                reorder = True
        self.entities_to_add.clear()

        # Reorder draw order if necessary
        if reorder:
            self.update_draw_order()

    def clear(self):
        """
        Clear the camera surface
        """
        self.camera.clear()

    def draw(self, surface: pygame.Surface):
        self.camera.clear()
        debugMode = bf.ResourceManager().get_sharedVar("debug_mode")
        # Draw entities in the correct order
        for uid in self.draw_order:
            if uid in self.entities and not self.entities[uid].drawn_by_group:  # Ensure the entity still exists
                self.entities[uid].draw(self.camera)

        # Draw debug outlines if in debug mode
        if debugMode == bf.debugMode.OUTLINES:
            [self.debug_entity(uid) for uid in self.draw_order if uid in self.entities]

        # Blit the camera surface onto the provided surface
        # surface.blit(self.camera.surface, (0, 0))
        self.camera.draw(surface)

    def update_draw_order(self):
        self.draw_order = sorted(
            (k for k,v in self.entities.items() if isinstance(v,Drawable) and not v.drawn_by_group),
            key= lambda uid : self.entities[uid].render_order
        )

    def debug_entity(self, uid: int):
        entity = self.entities[uid]
        def draw_rect(data):
            if data is None:
                return
            if isinstance(data, pygame.FRect) or isinstance(data, pygame.Rect):
                rect = data
                color = entity.debug_color
            else:
                rect = data[0]
                color = data[1]
            if self.camera.intersects(rect):
                pygame.draw.rect(self.camera.surface, color, self.camera.world_to_screen(rect), 1)

        for data in entity.get_debug_outlines():
            draw_rect(data)

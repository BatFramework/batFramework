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
        self.entity_to_add = set()
        self.entity_to_remove = set()
        self.draw_order : list[int] = []
        self.camera = bf.Camera(convert_alpha=convert_alpha)

    def set_clear_color(self,color):
        self.camera.set_clear_color(color)

    def set_scene(self, scene:BaseScene):
        self.scene = scene

    def _add(self,*entities:Entity):
        for e in entities:
            if e.uid not in self.entities and e not in self.entity_to_add:
                self.entity_to_add.add(e)
                e.set_parent_scene(self.scene)
                e.set_parent_layer(self)

    def get_by_tags(self,*tags)->list[Entity]:
        return [v for k,v in self.entities.items() if v.has_tags(tags) ]

    def get_by_uid(self,uid:int)->Entity|None:
        return self.entities.get(uid,None)

    def _remove(self,*entities:Entity):
        for e in entities:
            if e.uid in self.entities and e not in self.entity_to_remove:
                self.entity_to_remove.add(e)
                e.set_parent_scene(None)

    def process_event(self,event:pygame.Event):
        for e in self.entities.values():
            e.process_event(event)
            if event.consumed : return

    def update(self,dt):
        
        for e in self.entities.values():
            e.update(dt)
        for e in self.entity_to_remove:
            self.entities.pop(e.uid)
        self.entity_to_remove.clear()
        reorder = False
        for e in self.entity_to_add:
            self.entities[e.uid] = e
            if not reorder and isinstance(e,Drawable):
                reorder = True
        self.entity_to_add.clear()
        if reorder:
            self.update_draw_order()
        self.camera.update(dt)

    def clear(self):
        """
        Clear the camera surface
        """
        self.camera.clear()

    def draw(self,surface:pygame.Surface):
        debugMode = bf.ResourceManager().get_sharedVar("debug_mode")

        for uid in self.draw_order:
            self.entities[uid].draw(self.camera)

        if debugMode == bf.debugMode.OUTLINES:
            [self.debug_entity(uid) for uid in self.draw_order]

        surface.blit(self.camera.surface,(0,0))

    def update_draw_order(self):
        self.draw_order = sorted(
            (k for k,v in self.entities.items() if isinstance(v,Drawable)),
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

        [draw_rect(data) for data in entity.get_debug_outlines()]
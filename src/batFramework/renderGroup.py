import batFramework as bf
import pygame
from typing import Self
import multiprocessing
"""

+ same render order
+ fblits
- do_when_added not propagated if added after renderGroup is added

"""

class RenderGroup(bf.Entity):
    def __init__(self,*entities,blit_flags:int=0)->None:
        super().__init__(no_surface=True)
        self.entity_list : list[bf.Entity] = list(entities) if entities else []
        self.added:bool = False
        self.set_blit_flags(blit_flags)
        self.set_debug_color("white")

    def set_blit_flags(self,blit_flags)->Self:
        super().set_blit_flags(blit_flags)
        for entity in self.entity_list : 
            entity.set_bit_flags(blit_flags)
        return self
    
    def add_entity(self,*entities)->Self:
        if not entities:return self
        if entities : self.entity_list.extend(list(entities))
        if not self.parent_scene and not self.added:return self
        for e in self.entity_list:
            if self.parent_scene:  e.set_parent_scene(self.parent_scene)
            if self.added : e.do_when_added()
        self.sort_entity_list()
        self.rect = self.entity_list[0].rect.unionall_ip((e.rect for e in self.entity_list[1:]))
        for entity in entities : 
            entity.set_bit_flags(self.blit_flags)
        return self

    def remove_entity(self,*entity)->Self:
        for e in entity:
            if e not in self.entity_list: continue
            e.set_parent_scene(None)
            e.do_when_removed()
        self.entity_list = [e for e in self.entity_list if e not in entity]
        if not self.entity_list:
            self.rect.update(0,0,0,0)
        else:
            self.rect = self.entity_list[0].rect.unionall_ip((e.rect for e in self.entity_list[1:]))

        return self
    
    def get_bounding_box(self):
        yield (self.rect, self.debug_color)
        for e in self.entity_list:
            yield from e.get_bounding_box()

    def set_parent_scene(self, scene) -> Self:
        self.parent_scene = scene
        for e in self.entity_list:
            e.set_parent_scene(scene)
        return self

    def do_when_added(self):
        for e in self.entity_list:
            e.do_when_added()
        self.added = True

    def do_when_removed(self):
        for e in self.entity_list:
            e.do_when_removed()

    def process_event(self, event: pygame.Event) -> bool:
        """
        Returns bool : True if the method is blocking (no propagation to next children of the scene)
        """
        self.do_process_actions(event)
        res = self.do_handle_event(event)
        self.do_reset_actions()
        if  res : return res 
        for e in self.entity_list:
            res = e.process_event(event)
            if res : return res
        return False

    def update(self, dt: float)->None:
        """
            Update method to be overriden by subclasses of entity
        """
        if self.entity_list:
            for e in self.entity_list:
                e.update(dt)
            self.rect = self.entity_list[0].rect.unionall([e.rect for e in self.entity_list[1:]])

        self.do_update(dt)
        

    def sort_entity_list(self)->None:
        self.entity_list.sort(key=lambda e: e.render_order)
        
    def draw(self, camera: bf.Camera) -> int:
        """
            Draw the entity onto the camera with coordinate transposing
        """
        if not self.visible or not camera.intersects(self.rect):return 0
        # gen = filter(lambda e,camera=camera: self.should_draw(e,camera),self.entity_list)
        self.sort_entity_list()
        fblits_data = map(lambda e : (e.surface,camera.transpose(e.rect)),self.entity_list)
        camera.surface.fblits(fblits_data,self.blit_flags)    
        return 1



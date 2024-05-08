import batFramework as bf
import pygame
from typing import Self,Iterator,Callable
import multiprocessing
"""

+ same render order
+ fblits
- do_when_added not propagated if added after renderGroup is added

"""

class RenderGroup(bf.Entity):
    def __init__(self, iterator_func : Callable ,blit_flags:int=0)->None:
        super().__init__(no_surface=True)
        self.added:bool = False
        self.iterator = iterator_func
        self.set_blit_flags(blit_flags)
        self.set_debug_color("white")
        


    
    def get_bounding_box(self):
        yield (self.rect, self.debug_color)
        for e in self.iterator():
            yield from e.get_bounding_box()

    def set_parent_scene(self, scene) -> Self:
        self.parent_scene = scene
        for e in self.iterator():
            e.set_parent_scene(scene)
        return self

    def do_when_added(self):
        for e in self.iterator():
            e.do_when_added()
        self.added = True

    def do_when_removed(self):
        for e in self.iterator():
            e.do_when_removed()

    def process_event(self, event: pygame.Event) -> bool:
        """
        Returns bool : True if the method is blocking (no propagation to next children of the scene)
        """
        self.do_process_actions(event)
        res = self.do_handle_event(event)
        self.do_reset_actions()
        if  res : return res 
        for e in self.iterator():
            res = e.process_event(event)
            if res : return res
        return False

    def update(self, dt: float)->None:
        """
            Update method to be overriden by subclasses of entity
        """
        for e in self.iterator():
            e.update(dt)
        gen = self.iterator()
        self.rect = next(gen).rect.unionall([e.rect for e in gen])

        self.do_update(dt)
        

        
    def draw(self, camera: bf.Camera) -> int:
        """
            Draw the entity onto the camera with coordinate transposing
        """
        if not self.visible or not camera.intersects(self.rect):return 0
        # gen = filter(lambda e,camera=camera: self.should_draw(e,camera),self.entity_list)
        fblits_data = map(lambda e : (e.surface,camera.transpose(e.rect)),self.iterator())
        camera.surface.fblits(fblits_data,self.blit_flags)    
        return 1



import batFramework as bf
import pygame
from typing import List, Dict, Tuple, Union, Optional, Self, Callable, Any
from .animation import Animation

class AnimatedSprite(bf.Drawable):
    def __init__(self,*args,**kwargs) -> None:
        super().__init__(None, no_surface=True,*args,**kwargs)
        self.animations : dict[str,Animation] = {}
        self.counter = 0 # int counter
        self._fcounter = 0.0 # counter
        self.current_animation : str = None
        self.end_callback : Callable[[],Any] = None
        self._flipX : bool = False 

    @property
    def flipX(self)->bool:
        return self._flipX
    
    @flipX.setter
    def flipX(self,value:bool):
        self._flipX = value

    def set_end_callback(self,callback : Callable[[],Any]):
        self.end_callback = callback 

    def add_animation(self,name:str,animation:Animation)->Self:
        self.animations[name] = animation
        if self.rect.size == (0,0):
            self.rect.size = animation.frames[0].get_size()
        return self
    
    def set_animation(self,name:str,reset_counter:bool=True):
        if name not in self.animations :
            raise ValueError
        self.current_animation = name
        if reset_counter:
            self._fcounter = 0

    def get_current_frame(self)->int|None:
        if not self.current_animation:
            return None
        return  self.animations[self.current_animation].counter_to_frame(self._fcounter)        

    def update(self, dt):
        super().update(dt)        
        if not self.current_animation:
            return
        self._fcounter += dt
        self.counter = int(self._fcounter)
        if self.counter >= self.animations[self.current_animation].numFrames:
            if self.end_callback:
                self.end_callback()
            

    def draw(self, camera):
        self.surface.blit(self.animations[self.current_animation].get_frame(self.counter,self.flipX),(0,0))
        super().draw(camera)
        
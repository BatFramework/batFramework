import batFramework as bf
import pygame
from typing import List, Dict, Tuple, Union, Optional, Self, Callable, Any
from .animation import Animation

class AnimatedSprite(bf.Drawable):
    def __init__(self,*args,**kwargs) -> None:
        super().__init__((0,0),*args,**kwargs)
        self.animations : dict[str,Animation] = {}
        self.counter = 0 # int counter
        self._fcounter = 0.0 # counter
        self.current_animation : str = None
        self.end_callback : Callable[[],Any] = None
        self._flipX : bool = False
        self.animation_loop : int = -1
        self.queued_animation : str = None

    @property
    def flipX(self)->bool:
        return self._flipX
    
    @flipX.setter
    def flipX(self,value:bool):
        self._flipX = value

    def set_animation_end_callback(self,callback : Callable[[],Any]):
        self.end_callback = callback 

    def add_animation(self,animation:Animation)->Self:
        self.animations[animation.name] = animation
        if self.rect.size == (0,0):
            self.rect.size = animation.frames[0].get_size()
            self.surface = animation.frames[0].copy()
        return self
    
    def set_animation(self,name:str,reset_counter:bool=True,loop:int=-1,queued_animation:str=None):
        """
        Sets the current animation,
        if animation with given name hasn't been added, nothing happens
        """
        if name not in self.animations :
            return
        self.current_animation = name
        if reset_counter:
            self._fcounter = 0
            self.counter = 0
        self.animation_loop = loop
        if loop != -1:
            self.queued_animation = queued_animation
        else:
            self.queued_animation = None

    def get_current_frame(self)->int|None:
        if not self.current_animation:
            return None
        return  self.animations[self.current_animation].counter_to_frame(self._fcounter)        

    def update(self, dt):
        super().update(dt)        
        if not self.current_animation:
            return
        self._fcounter += dt * 60 
        self.counter = int(self._fcounter)
        # self.counter = self.get_current_frame()
        # print(f"{self.current_animation}:{self.counter}/{self.animations[self.current_animation].duration_list_length}")
        if self.counter >= self.animations[self.current_animation].duration_list_length:
            #one animation cycle ended
            if self.animation_loop > 0:
                self.animation_loop -= 1
            elif self.queued_animation is not None:
                # print("set to queued :",self.queued_animation)
                self.set_animation(self.queued_animation,True)

            if self.end_callback:
                self.end_callback()            
 
    def draw(self, camera):
        # print(self.current_animation, f"{self.counter}/{self.animations[self.current_animation].duration_list_length}")
        self.surface = self.animations[self.current_animation].get_frame(self.counter,self.flipX)#,(0,0)
        super().draw(camera)
        
import batFramework as bf
import pygame
from typing import List, Dict, Tuple, Union, Optional, Self, Callable, Any
from .animation import Animation

class AnimatedSprite(bf.Drawable):

    def __init__(self,*args,sprite_rect_anchor : bf.enums.alignment=bf.enums.alignment.CENTER, sprite_rect_offset:tuple[float]=None,**kwargs) -> None:
        super().__init__((0,0),*args,**kwargs)
        self._animations : dict[str,Animation] = {}
        self._animation : Animation|None = None
        
        self._flip : tuple[bool,bool] = [False,False]
        
        self._queued_animation : str = None
        self._frame_number : int = 0
        self.sprite_rect = self.rect.copy()
        self.sprite_rect_anchor = sprite_rect_anchor
        self.sprite_rect_offset = sprite_rect_offset if sprite_rect_offset else (0,0)

    def get_debug_outlines(self):
        yield from super().get_debug_outlines()
        yield (self.sprite_rect,"blue")
        
    @property
    def frame_number(self):
        return self._animation.frame_number if self._animation else None

    @property
    def flipX(self)->bool:
        return self._flip[0]
    
    @flipX.setter
    def flipX(self,value:bool):
        self._flip[0] = value

    @property
    def flipY(self)->bool:
        return self._flip[1]
    
    @flipY.setter
    def flipY(self,value:bool):
        self._flip[1] = value

    @property
    def animation(self)->Animation | None:
        return self._animation

    def add_animation(self,animation:Animation)->Self:
        self._animations[animation.name] = animation
        animation.set_end_callback(self._on_animation_end)
        animation.set_frame_callback(self._on_animation_frame)
        
        if self.sprite_rect.size == (0,0):
            first_frame = animation.get_frame(0)
            self.sprite_rect.size = first_frame.get_size()
            self.surface = first_frame.copy()
        return self

    def get_animation(self,name:str)->Animation | None:
        res = self._animations.get(name)
        return res

    
    def set_animation(self,name:str,reset_counter:bool=True,loop:int=-1,queued_animation:str=None):
        """
        Sets the current animation,
        if animation with given name hasn't been added, nothing happens
        queued animation plays after 'loop' number of animations (first one doesn't countz)
        if loop is negative, animation loops indefinitely and queued_animation is ignored
        
        """
        
        self._animation = self._animations.get(name)
        if self._animation is None:
            return
        if reset_counter:
            self._animation.reset_counter()
        self._animation_loop = loop
        if loop >= 0:
            self._queued_animation = queued_animation
        else:
            self._queued_animation = None

    def _on_animation_end(self):
        if self._queued_animation is not None:
            self.set_animation(self._queued_animation,True)

    def _on_animation_frame(self,frame:int):
        pass
        
    def update(self, dt):
        super().update(dt)        
        if self._animation is None:
            return
        self._animation.update(dt)
        setattr(self.sprite_rect,self.sprite_rect_anchor.value,getattr(self.rect,self.sprite_rect_anchor.value))
        self.sprite_rect.move_ip(*self.sprite_rect_offset)
        
    
    def draw(self, camera):
        if not self.animation : return
        self.surface = self._animation.get_frame(self._animation.frame_number,*self._flip)
        if not self.visible or self.drawn_by_group or not camera.world_rect.colliderect(self.sprite_rect) or self.surface.get_alpha() == 0:
            return
        camera.surface.blit(
            self.surface,
            camera.world_to_screen(self.sprite_rect),
            special_flags=self.blit_flags,
        )
        

import batFramework as bf
import pygame
from typing import List, Dict, Tuple, Union, Optional, Self
from .animation import Animation

class AnimatedSprite(bf.Drawable):
    def __init__(self, size: Optional[Tuple[int, int]] = None,*args,**kwargs) -> None:
        super().__init__(size, no_surface=True,*args,**kwargs)
        self.float_counter: float = 0
        self.animations: Dict[str, Animation] = {}
        self.current_state: Optional[Animation] = None
        self.flipX: bool = False
        self._locked: bool = False
        self._paused: bool = False
        self.animation_end_callback = None
        self.transition_end_animation = None

    def set_animation_end_callback(self,callback)->Self:
        self.animation_end_callback = callback
        return self

    @property
    def paused(self) -> bool:
        return self._paused

    @paused.setter
    def paused(self, value: bool) -> None:
        self._paused = value

    def toggle_pause(self) -> None:
        self.paused = not self.paused

    def set_counter(self, value: float) -> None:
        self.float_counter = value

    def set_frame(self, frame_index: int) -> None:
        if not self.current_state:
            return
        self.set_counter(sum(self.current_state.duration_list[:frame_index]))

    def lock(self) -> None:
        self._locked = True

    def unlock(self) -> None:
        self._locked = False

    def set_flipX(self, value: bool) -> None:
        self.flipX = value

    def remove_animation(self, name: str) -> bool:
        if name not in self.animations:
            return False
        self.animations.pop(name)
        if self.current_state and self.current_state.name == name:
            self.current_state = (
                list(self.animations.values())[0] if self.animations else None
            )
        return True

    def add_animation(
        self,
        animation:Animation
    ) -> bool:
        if animation.name in self.animations:
            return False
        self.animations[animation.name] = animation
        return True

    def set_animation(
        self, state: str, reset_counter: bool = True, lock: bool = False
    ) -> bool:
        if state not in self.animations or self._locked:
            return False
        
        animation = self.animations[state]
        self.current_state = animation

        if self.current_state.frames:
            self.rect = self.current_state.frames[0].get_frect(center=self.rect.center)

        if reset_counter or (self.float_counter > animation.duration_list_length):
            self.float_counter = 0

        if lock:
            self.lock()
        
        if self.transition_end_animation is not None:
            self.transition_end_animation = None
        return True
    
    def transition_to_animation(self,transition:str,animation:str)->Self:
        self.set_animation(transition)
        self.transition_end_animation = animation
        return self
    
    def get_current_animation(self) -> Optional[Animation]:
        return self.current_state

    def update(self, dt: float) -> None:
        s = self.get_current_animation()
        if  self.animations and s is not None:
            if not self.paused:
                self.float_counter += 60 * dt
                if self.float_counter > s.duration_list_length:
                    if self.transition_end_animation is not None:
                        # print(f"{self.transition_end_animation=}, {self.get_current_animation()=}")
                        self.set_animation(self.transition_end_animation)
                    if self.animation_end_callback is not None:
                        self.animation_end_callback()
                    self.float_counter = 0
        super().update(dt)


    def get_current_frame(self)->pygame.Surface:
        return self.current_state.get_frame(self.float_counter, self.flipX)

    def draw(self, camera: bf.Camera) -> None:
        if (
            not self.visible
            or not camera.rect.colliderect(self.rect)
            or not self.current_state
        ):
            return
        camera.surface.blit(
            self.get_current_frame(),
            camera.world_to_screen(self.rect),
        )
        return 

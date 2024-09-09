import batFramework as bf
import pygame
from typing import List, Dict, Tuple, Union, Optional, Self


def search_index(target: int, lst: List[int]) -> int:
    cumulative_sum = 0
    for index, value in enumerate(lst):
        cumulative_sum += value
        if cumulative_sum >= target:
            return index
    return -1


class Animation:
    def __init__(
        self,
        name: str
    ) -> None:
        self.name = name
        self.frames: list[pygame.Surface] = []
        self.frames_flipX : list[pygame.Surface] = []
        self.duration_list = []
        self.duration_list_length = 1

    def from_surface(self,surface:pygame.Surface,size : Tuple[int,int])->Self:
        self.frames         : List[pygame.Surface] = list(bf.utils.split_surface(surface, size).values())
        self.frames_flipX   : List[pygame.Surface] = list(bf.utils.split_surface(surface, size,func=lambda s : pygame.transform.flip(s,True,False)).values())
        return self

    def __repr__(self):
        return f"Animation({self.name})"

    def counter_to_frame(self, counter: Union[float, int]) -> int:
        if not self.frames : 
            raise ValueError("Animation has no frames")
        return search_index(
            int(counter % self.duration_list_length), self.duration_list
        )

    def get_frame(self, counter: Union[float, int], flip: bool) -> pygame.Surface:
        i = self.counter_to_frame(counter)
        return self.frames_flipX[i] if flip else self.frames[i]

    def set_duration_list(self, duration_list: Union[List[int], int]) -> Self:
        if isinstance(duration_list, int):
            duration_list = [duration_list] * len(self.frames)
        if len(duration_list) != len(self.frames):
            raise ValueError("duration_list should have values for all frames")
        self.duration_list = duration_list
        self.duration_list_length = sum(self.duration_list)
        return self

class AnimatedSprite(bf.Entity):
    def __init__(self, size: Optional[Tuple[int, int]] = None) -> None:
        super().__init__(size, no_surface=True)
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

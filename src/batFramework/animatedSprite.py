import batFramework as bf
import pygame
from typing import List, Dict, Tuple, Union, Optional
from enum import Enum


def search_index(target: int, lst: List[int]) -> int:
    cumulative_sum = 0
    for index, value in enumerate(lst):
        cumulative_sum += value
        if cumulative_sum >= target:
            return index
    return -1


class AnimState:
    def __init__(
        self,
        name: str,
        surface: pygame.Surface,
        size: Tuple[int,int],
        duration_list: Union[List[int], int],
    ) -> None:
        self.frames: List[pygame.Surface] = list(
            bf.utils.split_surface(
                surface, size
            ).values()
        )
        self.frames_flipX: List[pygame.Surface] = list(
            bf.utils.split_surface(surface, size,).values()
        )

        self.name = name
        self.set_duration_list(duration_list)

    def __repr__(self):
        return f"AnimState({self.name})"

    def counter_to_frame(self, counter: Union[float, int]) -> int:
        return search_index(
            int(counter % self.duration_list_length), self.duration_list
        )

    def get_frame(self, counter: Union[float, int], flip: bool) -> pygame.Surface:
        i = self.counter_to_frame(counter)
        return self.frames_flipX[i] if flip else self.frames[i]

    def set_duration_list(self, duration_list: Union[List[int], int]):
        if isinstance(duration_list, int):
            duration_list = [duration_list] * len(self.frames)
        if len(duration_list) != len(self.frames):
            raise ValueError("duration_list should have values for all frames")
        self.duration_list = duration_list
        self.duration_list_length = sum(self.duration_list)


class AnimatedSprite(bf.Entity):
    def __init__(self, size: Optional[Tuple[int, int]] = None) -> None:
        super().__init__(size, no_surface=True)
        self.float_counter: float = 0
        self.animStates: Dict[str, AnimState] = {}
        self.current_state: Optional[AnimState] = None
        self.flipX: bool = False
        self._locked: bool = False
        self._paused: bool = False

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

    def remove_animState(self, name: str) -> bool:
        if name not in self.animStates:
            return False
        self.animStates.pop(name)
        if self.current_state and self.current_state.name == name:
            self.current_state = (
                list(self.animStates.values())[0] if self.animStates else None
            )
        return True

    def add_animState(
        self,
        name: str,
        surface: pygame.Surface,
        size: Tuple[int, int],
        duration_list: Union[List[int], int],
    ) -> bool:
        if name in self.animStates:
            return False
        self.animStates[name] = AnimState(
            name, surface, size, duration_list
        )
        if len(self.animStates) == 1:
            self.set_animState(name)
        return True

    def set_animState(
        self, state: str, reset_counter: bool = True, lock: bool = False
    ) -> bool:
        if state not in self.animStates or self._locked:
            return False

        animState = self.animStates[state]
        self.current_state = animState

        self.rect = self.current_state.frames[0].get_rect(center=self.rect.center)

        if reset_counter or self.float_counter > animState.duration_list_length:
            self.float_counter = 0
        if lock:
            self.lock()
        return True

    def get_animState(self) -> Optional[AnimState]:
        return self.current_state

    def update(self, dt: float) -> None:
        s = self.get_animState()
        if  self.animStates and s is not None:
            if not self.paused:
                self.float_counter += 60 * dt
                if self.float_counter > s.duration_list_length:
                    self.float_counter = 0
        self.do_update(dt)

    def draw(self, camera: bf.Camera) -> None:
        if (
            not self.visible
            or not camera.rect.colliderect(self.rect)
            or not self.current_state
        ):
            return
        camera.surface.blit(
            self.current_state.get_frame(self.float_counter, self.flipX),
            camera.world_to_screen(self.rect),
        )
        return 

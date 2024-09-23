import pygame
import batFramework as bf
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

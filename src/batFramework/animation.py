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
        """
        Class to hold 2D animation data.
        All frames are expected to have the same size.
        This class does not do anything on its own, but can be used to easily manage
        multiple animations using a simple counter.
        The duration list provides a entry point for tweaking the timings,
        so image data can be saved (no need for contiguous duplicate frames)
        """
        self.name = name
        self.frames: list[pygame.Surface] = []
        self.frames_flipX : list[pygame.Surface] = []
        self.duration_list = []
        self.duration_list_length = 0 # prevents calling len() each frame
        self.numFrames : int = 0

    def from_surface(self,surface:pygame.Surface,frame_size : Tuple[int,int])->Self:
        """
        Loads frames from a spritesheet containing all animation frames aligned horizontally, left to right
        Frames are cut and stored in 2 versions, original and flipped on the horizontal axis.
        Flipping sprites being pretty common, this serves as a builtin cache.
        """
        self.frames : List[pygame.Surface] = list(
            bf.utils.split_surface(surface, frame_size).values()
        )
        self.frames_flipX : List[pygame.Surface] = list(
            bf.utils.split_surface(
                surface, frame_size,
                func=lambda s : pygame.transform.flip(s,True,False)
            ).values()
        )
        self.duration_list_length = len(self.frames)
        self.numFrames = self.duration_list_length
        if not self.duration_list:
            self.duration_list = [1]*self.duration_list_length
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
        if len(duration_list) != self.numFrames:
            raise ValueError("duration_list should have values for all frames")
        self.duration_list = duration_list
        self.duration_list_length = sum(self.duration_list)
        return self

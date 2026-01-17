import pygame
import batFramework as bf
from typing import List, Dict, Tuple, Union, Optional, Self, Iterable, Callable, Any





class Animation:
    def __init__(
        self,
        name: str
    ) -> None:
        """
        Class to store 2D animation data.
        All frames are expected to have the same size.
        This class is not intended to be used on its own, but can be used to easily manage
        multiple animations using a simple counter.
        The duration list provides a entry point for tweaking the timings,
        so image data can be saved (no need for contiguous duplicate frames)
        """
        self.name = name
        self._frames: list[pygame.Surface] = []
        self._cached_flip : dict[tuple[bool,bool],pygame.Surface] = {}
        self._duration_list = []
        self._duration_list_length = 0

        
        self._frame_callback :None|Callable[[int],Any] = None
        self._end_callback : None|Callable[[Any],Any]  = None

        self._counter : float = 0 # float counter for the animation
        self._frame_number :int = 0 # current frame number
        self._previous_frame_number : int = 0
        self._loop : int = 0

    @property
    def frame_number(self)->int|None:
        return self._frame_number


    def __repr__(self):
        return f"Animation({self.name})"
        
    def set_frame_callback(self,callback :None| Callable[[int],Any])->Self:
        self._frame_callback = callback
        return self

    def set_end_callback(self, callback: None|Callable[[Any],Any] )->Self:
        self._end_callback = callback
        return self

    @staticmethod
    def _search_index(target: int, lst: List[int]) -> int:
        cumulative_sum = 0
        for index, value in enumerate(lst):
            cumulative_sum += value
            if cumulative_sum >= target:
                return index
        return -1

    def from_surface(self,surface:pygame.Surface,frame_size : Tuple[int,int])->Self:
        """
        Loads frames from a spritesheet containing all animation frames aligned horizontally, left to right
        Frames are cut and stored in 2 versions, original and flipped on the horizontal axis.
        Flipping sprites being pretty common, this serves as a builtin cache.
        """
        self._frames : List[pygame.Surface] = list(
            bf.utils.split_surface(surface, frame_size).values()
        )
        self._cached_flip = {}
        self._duration_list_length = len(self._frames)
        if not self._duration_list:
            self._duration_list = [1]*self._duration_list_length
        return self

    def from_path(
        self,
        path: str,
        frame_size: Tuple[int, int],
        convert_alpha: bool = True
    ) -> Self:
        """
        Loads frames from a spritesheet at the given path.
        Uses ResourceManager to load the image.
        """
        surface = bf.ResourceManager().get_image(path, convert_alpha)
        return self.from_surface(surface, frame_size)

    def counter_to_frame(self, counter: Union[float, int]) -> int:
        if not self._frames : 
            raise ValueError("Animation has no frames")
        return self._search_index(
            int(counter % sum(self._duration_list)), self._duration_list
        )
 
    def get_frame(self, counter: Union[float, int], flipX: bool = False, flipY: bool = False) -> pygame.Surface|None:
        if not self._frames : return None
        original = self._frames[self._frame_number]
        if (not flipX) and (not flipY):
            return original
        frame = self._cached_flip.get((self._frame_number,flipX,flipY))
        if not frame:
            frame = pygame.transform.flip(original, flipX,flipY)
            self._cached_flip[(self._frame_number,flipX,flipY)] = frame
        return frame

    def set_duration_list(self, duration_list: Union[List[int], int]) -> Self:
        if not isinstance(duration_list, Iterable):
            duration_list = [duration_list] * len(self._frames)
        if len(duration_list) != self._duration_list_length:
            raise ValueError("duration_list should have values for all frames")
        self._duration_list = duration_list
        self._duration_list_length = len(duration_list)
        return self

    def reset_counter(self):
        self._counter = 0
        self._frame_number = 0
        
    def update(self, dt:float)->None:
        self._counter += dt * 60 
        self._frame_number = self.counter_to_frame(self._counter)
        if self._counter >= sum(self._duration_list):
            #one animation cycle ended
            if self._loop > 0:
                self._loop -= 1

            if self._end_callback:
                self._end_callback()
                
        if self._frame_number != self._previous_frame_number:
            self._previous_frame_number = self._frame_number
            if self._frame_callback:
                self._frame_callback(self._frame_number)

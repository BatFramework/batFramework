from enum import Enum
import pygame
import batFramework as bf
from functools import lru_cache


class Easing(Enum):
    EASE_IN = (0.12, 0, 0.39, 0)
    EASE_OUT = (0.61, 1, 0.88, 1)
    EASE_IN_OUT = (0.37, 0, 0.63, 1)
    EASE_IN_OUT_ELASTIC = (0.7, -0.5, 0.3, 1.5)
    LINEAR = (1, 1, 0, 0)
    # Add more easing functions as needed

    def __init__(self, *control_points):
        self.control_points = control_points


@lru_cache(maxsize=None)
def process_value(progress,p0,p1,p2,p3)->float:
    t = progress
    t_inv = 1.0 - t
    t2 = t * t
    t3 = t * t2
    t_inv2 = t_inv * t_inv
    return 3 * t_inv2 * t * p1 + 3 * t_inv * t2 * p3 + t3

class EasingAnimation(bf.Timer):
    def __init__(
        self,
        easing_function: Easing = Easing.LINEAR,
        duration: float = 1,
        update_callback=None,
        end_callback=None,
        loop: bool = False,
    )->None:
        self.easing_function = easing_function
        self.update_callback = update_callback
        self.value :float = 0.0
        super().__init__(duration, end_callback,loop)

    def get_value(self)->float:
        return self.value

    def start(self):
        super().start()
        self.value = 0

    def update(self,dt:float)->None:
        if self.get_progression() == 1 : return
        super().update(dt)
        self.value = process_value(self.get_progression(),*self.easing_function.control_points)
        if self.update_callback: self.update_callback(self.value)




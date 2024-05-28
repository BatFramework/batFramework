import pygame
import batFramework as bf
from functools import lru_cache
from .enums import easing


@lru_cache(maxsize=None)
def process_value(progress: float, p0: float, p1: float, p2: float, p3: float) -> float:
    if p0 == 0 and p1 == 0 and p2 == 1 and p3 == 1:  # Linear easing control points
        return progress
    t = progress
    t_inv = 1.0 - t
    t2 = t * t
    t3 = t * t2
    t_inv2 = t_inv * t_inv
    return 3 * t_inv2 * t * p1 + 3 * t_inv * t2 * p3 + t3


class EasingController(bf.Timer):
    def __init__(
        self,
        easing_function: easing = easing.LINEAR,
        duration: float = 1,
        update_callback=None,
        end_callback=None,
        loop: bool = False,
    ) -> None:
        self.easing_function = easing_function
        self.update_callback = update_callback
        self.value: float = 0.0
        super().__init__(duration, end_callback, loop)

    def get_value(self) -> float:
        return self.value

    def start(self, force: bool = False):
        super().start(force)
        self.value = 0

    def update(self, dt: float) -> None:
        if self.get_progression() == 1:
            return
        super().update(dt)
        if self.get_progression() == 0:
            return
        if self.easing_function == easing.LINEAR:
            self.value = self.get_progression()
        else:
            self.value = process_value(
                self.get_progression(), *self.easing_function.control_points
            )
        if self.update_callback:
            self.update_callback(self.value)

    def end(self):
        if self.update_callback:
            self.update_callback(1)
        super().end()

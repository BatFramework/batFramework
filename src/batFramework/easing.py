from enum import Enum
import pygame
import batFramework as bf


class Easing(Enum):
    EASE_IN = (0.12, 0, 0.39, 0)
    EASE_OUT = (0.61, 1, 0.88, 1)
    EASE_IN_OUT = (0.37, 0, 0.63, 1)
    EASE_IN_OUT_ELASTIC = (0.7, -0.5, 0.3, 1.5)
    LINEAR = (1, 1, 0, 0)
    # Add more easing functions as needed

    def __init__(self, *control_points):
        self.control_points = control_points


class EasingAnimation(bf.Timer):
    _cache = {}

    def __init__(
        self,
        name: str = None,
        easing_function: Easing = Easing.LINEAR,
        duration: int = 100,
        update_callback=None,
        end_callback=None,
        loop: bool = False,
        reusable: bool = False,
    ):
        self.easing_function = easing_function
        self.update_callback = update_callback
        self.value = 0.0
        super().__init__(name, duration, loop, end_callback, reusable)

    def get_value(self):
        return self.value

    def start(self):
        self.value = 0
        super().start()  # self.elapsed_progress set to 0 here

    def update(self) -> bool:
        if super().update():
            return True  # If timer ended now, end() is called. So don't process value.
        self._process_value()
        # if self.name == 0: print("UPDATING (callback) in easing")
        if self.update_callback:
            self.update_callback(self.value)
        return False

    def end(self):
        # Call update 1 last time with the last value

        self.elapsed_progress = 1
        self._process_value()
        if self.update_callback:
            self.update_callback(self.value)
        self.value = 0
        super().end()  # sets elapsed_progress to 0

    def _process_value(self):
        p0, p1, p2, p3 = self.easing_function.control_points
        cache_key = (self.elapsed_progress, p0, p1, p2, p3)
        if cache_key in EasingAnimation._cache:
            y = EasingAnimation._cache[cache_key]
        else:
            t = self.elapsed_progress
            t_inv = 1.0 - t
            t2 = t * t
            t3 = t * t2
            t_inv2 = t_inv * t_inv

            y = 3 * t_inv2 * t * p1 + 3 * t_inv * t2 * p3 + t3
            EasingAnimation._cache[cache_key] = y
        self.value = y

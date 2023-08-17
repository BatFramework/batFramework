from enum import Enum
import pygame
import batFramework as bf

class Easing(Enum):
    EASE_IN     = (0.12, 0, 0.39, 0)
    EASE_OUT    = (0.61, 1, 0.88, 1)
    EASE_IN_OUT = (0.37, 0, 0.63, 1)
    LINEAR      = (1, 1, 0, 0)
    # Add more easing functions as needed

    def __init__(self, *control_points):
        self.control_points = control_points


class EasingAnimation(bf.Timer):
    _cache = {}

    def __init__(
        self,name=None,
        easing_function:Easing=Easing.LINEAR,
        duration=100,
        update_callback=None,
        end_callback=None,
        loop=False,
    ):
        super().__init__(name=name,duration=duration,end_callback=end_callback,loop=loop)
        self.easing_function = easing_function
        self.update_callback = update_callback
        self.value = 0.0

    def update(self):
        if super().update(): return
        # Evaluate the cubic Bezier curve at the current progression (t)
        p0, p1, p2, p3 = self.easing_function.control_points
        cache_key = (self.progression, p0, p1, p2, p3)
        if cache_key in EasingAnimation._cache:
            y = EasingAnimation._cache[cache_key]
            # l =len(EasingAnimation._cache)
            # if l % 10 == 0 : print(l)
        else:
            # t = np.asarray(self.progression)
            t = self.progression
            t_inv = 1.0 - t
            t2 = t * t
            t3 = t * t2
            t_inv2 = t_inv * t_inv

            y = 3 * t_inv2 * t * p1 + 3 * t_inv * t2 * p3 + t3 * 1
            EasingAnimation._cache[cache_key] = y
            # print(len(EasingAnimation._cache))
        self.value = y
        if self.update_callback:
            self.update_callback(self.value)

    def end(self):
        super().end()
        self.value =  0

    def start(self):
        super().start()
        self.value =  0
    
    def get_value(self):
        return self.value


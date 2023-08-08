# import numpy as np
from enum import Enum
import pygame

class Easing(Enum):
    EASE_IN = (0.12, 0, 0.39, 0)
    EASE_OUT = (0.61, 1, 0.88, 1)
    EASE_IN_OUT = (0.37, 0, 0.63, 1)
    # Add more easing functions as needed

    def __init__(self, *control_points):
        self.control_points = control_points




class EasingAnimation:
    _cache = {}
    def __init__(self, easing_function, duration, update_callback=None, end_callback=None, loop=False):
        self.easing_function = easing_function
        self.duration = duration
        self.update_callback = update_callback
        self.end_callback = end_callback
        self.loop = loop
        self.start_time = None
        self.progression = None
        self.stopped = False

    def start(self):
        self.start_time = pygame.time.get_ticks()
        self.progression = 0.0

    def end(self):
        self.start_time = pygame.time.get_ticks()-self.duration

    def stop(self):
        self.stopped = True

    def update(self):
        if self.start_time is None or self.stopped:
            return False

        elapsed_time = pygame.time.get_ticks() - self.start_time
        self.progression = round(min(elapsed_time / self.duration, 1),2)

        # Evaluate the cubic Bezier curve at the current progression (t)
        p0, p1, p2, p3 = self.easing_function.control_points
        cache_key = (self.progression,p0,p1,p2,p3)
        if cache_key in EasingAnimation._cache:
            y= EasingAnimation._cache[cache_key]
            # l =len(EasingAnimation._cache) 
            # if l % 10 == 0 : print(l)
        else:
            # t = np.asarray(self.progression)
            t =self.progression
            t_inv = 1.0 - t
            t2 = t * t
            t3 = t * t2
            t_inv2 = t_inv * t_inv

            y =   3 * t_inv2* t * p1 + 3 * t_inv * t2 * p3 + t3 * 1
            EasingAnimation._cache[cache_key] = y
            # print(len(EasingAnimation._cache))


        if self.update_callback:
            self.update_callback(y)

        if self.progression >= 1.0:
            if self.end_callback:
                self.end_callback()
            if self.loop:
                self.start()
                return True
                
            return False

        return True

    def is_over(self):
        return self.start_time is not None and self.progression >= 1.0

    def reset(self):
        self.start_time = None
        self.progression = None

class EasingAnimationManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EasingAnimationManager, cls).__new__(cls)
            cls._instance.animations = []
        return cls._instance

    def create_animation(self, easing_function, duration, update_callback=None, end_callback=None, loop=False):
        animation = EasingAnimation(easing_function, duration, update_callback, end_callback, loop)
        self.animations.append(animation)
        return animation

    def update(self):
        animations_to_remove = []
        for animation in self.animations:
            if not animation.update():
                animations_to_remove.append(animation)

        # Remove finished animations
        for animation in animations_to_remove:
            self.animations.remove(animation)

    def is_empty(self):
        return len(self.animations) == 0

    def reset_animations(self):
        for animation in self.animations:
            animation.reset()

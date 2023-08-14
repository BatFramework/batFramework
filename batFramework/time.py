import pygame
import batFramework as bf


class Timer:
    def __init__(self, duration, loop=False) -> None:
        self.start_time = None
        self.stopped = False
        self.duration = duration
        self.loop = loop
        self.progression = 0.0
    def start(self):
        self.start_time = pygame.time.get_ticks()
        self.stopped = False
        self.progression =0.0

    def update(self):
        if self.progression <1:
            elapsed_time = pygame.time.get_ticks() - self.start_time
            self.progression = elapsed_time / self.duration

    def stop(self):
        self.stopped = True

    def end(self):
        self.progression = 1

    def ended(self):
        return (
            not self.stopped
            and  self.progression>= 1
            if self.start_time
            else False
        )


class Time(metaclass=bf.Singleton):
    def __init__(self):
        self.timers: dict[str, tuple[Timer, None]] = {}
        self._highest_count = 0

    def timer(self, name=None, duration=100, loop=False, callback=None) -> Timer:
        if not name:
            name = str(self._highest_count)
            self._highest_count += 1
        t = Timer(duration, loop)
        self.timers[name] = [t, callback]
        return t

    def update(self):
        to_remove = []
        for name, child in self.timers.copy().items():
            child[0].update()
            if child[0].ended():
                if child[1]:
                    child[1]()
                if child[0].loop:
                    child[0].start()
                    continue
                to_remove.append(name)

        for name in to_remove:
            self.timers.pop(name)

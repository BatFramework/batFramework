import pygame
import batFramework as bf


class Timer:
    _highest_count = 0

    def __init__(
        self,
        name=None,
        duration=1000,
        loop=False,
        end_callback=None,
        reusable: bool = False,
    ):
        # Initialize timer properties
        self.start_time = None
        self.stopped = True
        self.name = name if name is not None else self._highest_count
        Timer._highest_count += 1
        self.duration = duration
        self.loop = loop
        self.elapsed_progress = 0.0
        self.end_callback = end_callback
        self.reusable: bool = reusable

    def start(self):
        # Start the timer and set the start time
        if self.start_time is None:
            Time().add_timer(self)

        self.start_time = pygame.time.get_ticks()
        self.stopped = False
        self.elapsed_progress = 0.0

    def update(self):
        if self.stopped:
            return False
        current_time = pygame.time.get_ticks()
        if self.elapsed_progress < 1:
            # Calculate elapsed progress
            self.elapsed_progress = (current_time - self.start_time) / self.duration
            if self.elapsed_progress >= 1:
                # Timer has completed
                self.end()
                return True
        elif self.loop:
            # If looping, restart the timer
            self.start()
        return False

    def stop(self):
        # Stop the timer
        self.stopped = True

    def end(self):
        self.elapsed_progress = 1
        self.stopped = False
        if self.end_callback:
            self.end_callback()

    def ended(self):
        if self.start_time is None:
            return False
        return (
            (not self.loop)
            and (self.elapsed_progress >= 1)
            and (not self.stopped)
            and not self.reusable
        )


class TimeManager(metaclass=bf.Singleton):
    def __init__(self):
        # Initialize the Time class with a dictionary of timers
        self.timers = {}

    def add_timer(self, timer):
        # Add a timer to the dictionary
        self.timers[timer.name] = timer

    def update(self):
        # Update all timers and remove completed ones
        for timer in list(self.timers.values()):
            timer.update()

        to_remove = [name for name, timer in self.timers.items() if timer.ended()]

        for name in to_remove:
            # print(self.timers.pop(name).name,"removed !")
            self.timers.pop(name)

import pygame
import batFramework as bf

class Time:...
class Timer:
    _highest_count = 0
    def __init__(self,name=None, duration=1000, loop=False,end_callback=None) -> None:
        self.start_time = None
        self.stopped = False
        self.name = name
        if name is None:
            self.name = self._highest_count
            Timer._highest_count+=1
        self.duration = duration
        self.loop = loop
        self.progression = 0.0
        self.end_callback = end_callback
    def start(self):
        if self.start_time == None:
            Time().add_timer(self)
        self.start_time = pygame.time.get_ticks()
        self.stopped = False
        self.progression =0.0
        self.update()

    def update(self):

        if self.progression <1:
            elapsed_time = pygame.time.get_ticks() - self.start_time
            self.progression = elapsed_time / self.duration
            # print(self.name,self.progression)
            if self.progression >= 1:
                # print("GOB END",self.end_callback)
                self.end()
                return True
        elif self.loop : 
            self.start()
        return False
    def stop(self):
        self.stopped = True

    def end(self):
        self.progression = 1
        if self.end_callback : self.end_callback()
    def ended(self):
        if self.start_time: 
            return not self.loop and self.progression>=1 and self.stopped == False
        return False

class Time(metaclass=bf.Singleton):
    def __init__(self):
        self.timers : dict[str,Timer]= {}

    def add_timer(self, timer: Timer):
        self.timers[timer.name] = timer

    def update(self):
        for timer in list(self.timers.values()):
            timer.update()

        to_remove = [name for name, timer in self.timers.items() if timer.ended()]

        for name in to_remove:
            self.timers.pop(name)
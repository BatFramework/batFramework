import pygame
import batFramework as bf
from typing import Self

class Timer:
    _count :int = 0
    def __init__(self,duration:float|int,end_callback,loop:bool=False)->None:
        self.name = Timer._count
        Timer._count+=1
        self.end_callback = end_callback
        self.duration : int|float = duration
        self.paused : bool = False
        self.elapsed_time : int = -1
        self.over : bool = False  
        self.do_delete:bool = False
        self.is_looping :bool = loop 

    def stop(self)->Self:
        self.elapsed_time =-1
        self.over = False
        self.paused = False
        return self
    
    def start(self)->Self:
        if self.elapsed_time >= 0 : return self
        self.elapsed_time = 0
        self.paused = False
        self.over = False
        bf.TimeManager().add_timer(self)
        return self
        
    def pause(self)->Self:
        self.paused = True
        return self

    def resume(self)->Self:
        self.paused = False
        return self
    def delete(self)->Self:
        self.do_delete = True
        return self
    def get_progression(self)->float:
        if self.elapsed_time < 0 : return 0
        if self.elapsed_time >= self.duration: return 1
        return  self.elapsed_time / self.duration
        
    def update(self,dt)->None:
        if self.elapsed_time < 0 or self.paused: return
        self.elapsed_time += dt
        # print("update :",self.elapsed_time,self.duration)
        if self.get_progression() == 1:
            self.end()
            
    def end(self):
        self.end_callback()
        if self.is_looping:
            self.elapsed_time = -1
            self.start()
            return
            
        self.over = True

    def has_ended(self)->bool:
        return self.over or self.do_delete


class TimeManager(metaclass=bf.Singleton):
    def __init__(self):
        # Initialize the TimeManager class with a dictionary of timers
        self.timers = {}

    def add_timer(self, timer):
        # Add a timer to the dictionary
        self.timers[timer.name] = timer

    def update(self,dt):
        # Update all timers and remove completed ones
        timers = list(self.timers.values())
        for timer in [t for t in timers if not t.paused]:
            timer.update(dt)

        to_remove = [name for name, timer in self.timers.items() if timer.has_ended()]

        for name in to_remove:
            # print(self.timers.pop(name).name,"removed !")
            self.timers.pop(name)

import pygame
import batFramework as bf
from typing import Self

class Timer:
    _count :int = 0
    def __init__(self,duration:float|int,end_callback,loop:bool=False)->None:
        self.name = Timer._count
        Timer._count+=1
        
        self.duration : int|float = duration
        self.end_callback = end_callback

        self.elapsed_time : float = -1
        self.is_over : bool = False  
        self.is_looping :bool = loop
        self.is_paused : bool = False
        self.do_delete:bool = False
        
    def stop(self)->Self:
        self.elapsed_time =-1
        self.is_over = False
        self.is_paused = False
        return self
    
    def start(self,force:bool=False)->Self:
        if self.elapsed_time != -1 and not force: return self
        if not bf.TimeManager().add_timer(self) : return self
        self.elapsed_time = 0
        self.is_paused = False
        self.is_over = False
        return self
        
    def pause(self)->Self:
        self.is_paused = True
        return self

    def resume(self)->Self:
        self.is_paused = False
        return self
        
    def delete(self)->Self:
        self.do_delete = True
        return self

    def has_started(self)->bool:
        return self.elapsed_time != -1
        
    def get_progression(self)->float:
        if self.elapsed_time < 0 : return 0
        if self.elapsed_time >= self.duration: return 1
        return  self.elapsed_time / self.duration
        
    def update(self,dt)->None:
        if self.elapsed_time < 0 or self.is_paused or self.is_over: return
        self.elapsed_time += dt
        # print("update :",self.elapsed_time,self.duration)
        if self.get_progression() == 1:
            self.end()

    def end(self):
        if self.end_callback : self.end_callback()
        self.elapsed_time = -1
        self.is_over = True
        if self.is_looping:
            self.start()
            return

    def should_delete(self)->bool:
        return self.is_over or self.do_delete


class TimeManager(metaclass=bf.Singleton):
    def __init__(self):
        # Initialize the TimeManager class with a dictionary of timers
        self.registers = {
            "global":{"active":True,"timers":{}}
        }

    def add_register(self,register:str):
        self.registers[registers] = {"active":True,"timers":{}}

    def add_timer(self, timer,register:str="global")->bool:
        # Add a timer to the dictionary
        reg = self.registers.get(register,None)
        if reg is None : 
            print(f"Register 'register' does not exist !")
            return False
        self.registers[register]["timers"][timer.name] = timer
        # print("added")
        return True

    def get_active_registers(self):
        for reg in self.registers.values():
            if reg["active"] : 
                yield reg
    
    def update(self,dt):
        # Update all timers and remove completed ones
        for reg in self.get_active_registers():
            for name, timer in {k: v for k, v in reg["timers"].items() if not v.is_paused}.items():
                timer.update(dt)

            to_remove = [name for name, timer in reg["timers"].items() if timer.should_delete()]

            for name in to_remove:
                reg["timers"].pop(name)

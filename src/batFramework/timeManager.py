import batFramework as bf
from typing import Callable, Union, Self,Any


class Timer:
    _count: int = 0
    _available_ids: set[int] = set()

    def __init__(self, duration: Union[float, int], end_callback: Callable[[],Any], loop: bool = False, register: str = "global") -> None:
        if Timer._available_ids:
            self.uid = Timer._available_ids.pop()
        else:
            self.uid = Timer._count
            Timer._count += 1

        self.register = register
        self.duration: int | float = duration
        self.end_callback = end_callback

        self.elapsed_time: float = -1
        self.is_over: bool = False
        self.is_looping: bool = loop
        self.is_paused: bool = False
        self.do_delete: bool = False

    def __bool__(self)->bool:
        return self.elapsed_time==-1 or self.is_over

    def __str__(self) -> str:
        return f"Timer ({self.uid}) {self.elapsed_time}/{self.duration} | {'loop ' if self.is_looping else ''} {'(D) ' if self.do_delete else ''}"

    def stop(self) -> Self:
        self.elapsed_time = -1
        self.is_over = False
        self.is_paused = False
        return self

    def start(self, force: bool = False) -> Self:
        if self.elapsed_time != -1 and not force:
            return self
        if not bf.TimeManager().add_timer(self,self.register):
            return self
        self.elapsed_time = 0
        self.is_paused = False
        self.is_over = False
        return self

    def pause(self) -> Self:
        self.is_paused = True
        return self

    def resume(self) -> Self:
        self.is_paused = False
        return self

    def delete(self) -> Self:
        self.do_delete = True
        return self

    def has_started(self) -> bool:
        return self.elapsed_time != -1

    def get_progression(self) -> float:
        if self.elapsed_time < 0:
            return 0
        if self.elapsed_time >= self.duration:
            return 1
        return self.elapsed_time / self.duration

    def update(self, dt) -> None:
        if self.elapsed_time < 0 or self.is_paused or self.is_over:
            return
        self.elapsed_time += dt
        # print("update :",self.elapsed_time,self.duration)
        if self.get_progression() == 1:
            self.end()

    def end(self):
        if self.end_callback:
            self.end_callback()
        self.elapsed_time = -1
        self.is_over = True
        if self.is_looping:
            self.start()
            return

    def should_delete(self) -> bool:
        return self.is_over or self.do_delete

    def _release_id(self):
        Timer._available_ids.add(self.uid)


class SceneTimer(Timer):
    def __init__(self, duration: float | int, end_callback, loop: bool = False, scene_name:str = "global") -> None:
        super().__init__(duration, end_callback, loop, scene_name)

class TimeManager(metaclass=bf.Singleton):
    class TimerRegister:
        def __init__(self, active=True):
            self.active = active
            self.timers: dict[int | str, Timer] = {}

        def __iter__(self):
            return iter(self.timers.values())

        def add_timer(self, timer: Timer):
            self.timers[timer.uid] = timer

        def update(self, dt):
            expired_timers = []
            for timer in list(self.timers.values()):
                if not timer.is_paused:
                    timer.update(dt)
                if timer.should_delete():
                    expired_timers.append(timer.uid)
            for uid in expired_timers:
                self.timers[uid]._release_id()
                del self.timers[uid]

    def __init__(self):
        self.registers = {"global": TimeManager.TimerRegister()}

    def add_register(self, name, active=True):
        if name not in self.registers:
            self.registers[name] = TimeManager.TimerRegister(active)

    def add_timer(self, timer, register="global") -> bool:
        if register in self.registers:
            self.registers[register].add_timer(timer)
            return True
        print(f"Register '{register}' does not exist.")
        return False

    def get_active_registers(self) -> list[TimerRegister]:
        return [t for t in self.registers.values() if t.active]

    def update(self, dt):
        for register_name, register in self.registers.items():
            if register.active:
                register.update(dt)

    def activate_register(self, name, active=True):
        if name in self.registers:
            self.registers[name].active = active
        else:
            print(f"Register '{name}' does not exist.")

    def deactivate_register(self, name):
        self.activate_register(name, active=False)

    def __str__(self)->str:
        res = "" 
        for name,reg in self.registers.items():
            if not reg.timers:continue
            res +=name+"\n"
            for t in reg.timers.values():
                res +="\t"+str(t)+"\n"
        return res

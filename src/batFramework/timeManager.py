import batFramework as bf
from typing import Callable, Union, Self,Any

class Timer:
    _count: int = 0
    _available_ids: set[int] = set()

    def __init__(self, duration: float, end_callback: Callable[[], Any], loop: int = 0, register: str = "global") -> None:
        if Timer._available_ids:
            self.uid = Timer._available_ids.pop()
        else:
            self.uid = Timer._count
            Timer._count += 1

        self.register = register
        self.duration: float = duration
        self.end_callback = end_callback

        self.elapsed_time: float = 0
        self.is_over: bool = False
        self.loop: int = loop  # Number of loops (-1 for infinite)
        self.is_paused: bool = False
        self.do_delete: bool = False
        self.is_stopped: bool = True

    def __bool__(self) -> bool:
        return self.elapsed_time != -1 and self.is_over

    def __str__(self) -> str:
        loop_info = "infinite" if self.loop == -1 else f"{self.loop} loops left"
        return f"Timer ({self.uid}) {self.elapsed_time}/{self.duration} | {loop_info} {'(D) ' if self.do_delete else ''}"

    def stop(self) -> Self:
        """
        Cancels all progression and stops the timer.
        Does not mark it for deletion and does not call the end_callback.
        Prevents automatic restart if looping.
        """
        self.is_stopped = True
        self.is_paused = False
        self.is_over = False
        self.elapsed_time = 0
        return self

    def start(self, force: bool = False) -> Self:
        """
        Starts the timer only if not already started (unless force is used, which resets it).
        """
        if self.elapsed_time > 0 and not force:
            return self
        if not bf.TimeManager().add_timer(self, self.register):
            return self
        self.elapsed_time = 0
        self.is_paused = False
        self.is_over = False
        self.is_stopped = False
        return self

    def pause(self) -> Self:
        """
        Momentarily stops the timer until resume is called.
        """
        self.is_paused = True
        return self

    def resume(self) -> Self:
        """
        Resumes from a paused state.
        """
        self.is_paused = False
        return self

    def delete(self) -> Self:
        """
        Marks the timer for deletion.
        """
        self.do_delete = True
        return self

    def has_started(self) -> bool:
        """
        Returns True if the timer has started.
        """
        return not self.is_stopped

    def get_progression(self) -> float:
        """
        Returns the progression of the timer (0 to 1) as a float.
        """
        if self.is_stopped:
            return 0
        if self.elapsed_time >= self.duration:
            return 1
        return self.elapsed_time / self.duration

    def update(self, dt) -> None:
        if self.is_stopped or self.is_paused or self.is_over:
            return
        self.elapsed_time += dt
        if self.get_progression() == 1:
            self.end()

    def end(self):
        """
        Ends the timer progression (calls the end_callback function).
        Is called automatically once the timer is over.
        Will not mark the timer for deletion.
        If it is looping, it will restart the timer **only if it wasn't stopped**.
        """
        self.is_over = True
        if self.end_callback:
            self.end_callback()

        # Handle looping
        if self.loop == -1:  # Infinite looping
            self.elapsed_time = 0
            self.start()
            return
        elif self.loop > 0:  # Decrease loop count and restart
            self.loop -= 1
            self.elapsed_time = 0
            self.start()
            return

        # Stop the timer if no loops are left
        self.is_stopped = True

    def should_delete(self) -> bool:
        """
        Method that returns if the timer is to be deleted.
        Required for timer management.
        """
        return self.is_over or self.do_delete

    def _release_id(self):
        Timer._available_ids.add(self.uid)

class SceneTimer(Timer):
    """
    A timer that is only updated while the given scene is active (being updated)
    """
    def __init__(self, duration: float | int, end_callback, loop: int = 0, scene_name:str = "global") -> None:
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

    def remove_register(self, name):
        if name not in self.registers:
            return
        
        self.registers.pop(name)


    def add_timer(self, timer, register="global") -> bool:
        if register in self.registers:
            self.registers[register].add_timer(timer)
            return True
        print(f"Register '{register}' does not exist.")
        return False

    def get_active_registers(self) -> list[TimerRegister]:
        return [t for t in self.registers.values() if t.active]

    def update(self, dt):
        for register in self.registers.values():
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

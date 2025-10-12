from .label import Label
from typing import Self,Callable,Any
import batFramework as bf
import pygame
import sys


def convert_to_int(*args):
    return [int(arg) for arg in args]


class Debugger(Label):
    def __init__(self) -> None:
        super().__init__("")
        self.root_link = None
        self.static_data: dict[str,Any] = {}
        self.dynamic_data: dict[str,Callable[[],str]] = {}
        self.refresh_interval :float = .01
        self.refresh_counter: float = 0
        self.add_tags("debugger")
        self.set_visible(False)
    

    def set_parent(self, parent):
        super().set_parent(parent)
        self.root_link = self.get_root()
        
    def set_refresh_rate(self, value: float) -> Self:
        """
        seet refresh interval, time in seconds between each refresh of the debugger
        """
        self.refresh_interval = value
        self.refresh_counter = 0
        return self

    def add_static(self, key: str, data):
        self.static_data[key] = str(data)
        self.update_text()

    def add_dynamic(self, key: str, func:Callable[[],str]) -> None:
        self.dynamic_data[key] = func
        self.update_text()

    def remove_static(self, key:str) -> bool:
        try:
            self.static_data.pop(key)
            return True
        except KeyError:
            return False

    def remove_dynamic(self, key:str) -> bool:
        try:
            self.dynamic_data.pop(key)
            return True
        except KeyError:
            return False

    def set_parent_scene(self, scene) -> Self:
        super().set_parent_scene(scene)
        self.set_render_order(sys.maxsize-100)
        self.update_text()
        return self

    def set_text(self, text: str) -> Self:
        return super().set_text(text)

    def update_text(self) -> None:
        if not self.parent_scene:
            return

        d = "\n".join(
            key + ":" + data if key != "" else data
            for key, data in self.static_data.items()
        )

        d2 = "\n".join(
            key + ":" + str(data()) if key != "" else str(data())
            for key, data in self.dynamic_data.items()
        )

        self.set_text("\n".join((d, d2)).strip())

    def update(self, dt: float) -> None:
        if not self.parent_scene:
            return
        
        if bf.ResourceManager().get_sharedVar("debug_mode") != bf.debugMode.DEBUGGER:
            self.set_visible(False)
            return
        
        self.set_visible(True)
        self.refresh_counter = self.refresh_counter + dt
        
        if self.refresh_counter > self.refresh_interval:
            self.refresh_counter = 0
            self.update_text()


    def __str__(self) -> str:
        return "Debugger"

    def top_at(self, x, y):
        return None


class FPSDebugger(Debugger):
    def __init__(self):
        super().__init__()

    def do_when_added(self):
        if not self.parent_scene or not self.parent_scene.manager:
            print("Debugger could not link to the manager")
            return
        manager_link = self.parent_scene.manager
        self.add_dynamic("FPS", lambda: str(round(manager_link.get_fps())))


class BasicDebugger(FPSDebugger):

    def do_when_added(self):
        if not self.parent_scene or not self.parent_scene.manager:
            print("Debugger could not link to the manager")
            return
        self.add_dynamic(
            "Resolution", lambda: "x".join(str(i) for i in bf.const.RESOLUTION)
        )
        super().do_when_added()
        self.add_dynamic("Mouse", pygame.mouse.get_pos)

        if self.root_link is None:
            return
        

        self.add_dynamic(
            "Hover",
            lambda: (
                str(self.root_link.hovered) if self.root_link.hovered else None
            ),
        )


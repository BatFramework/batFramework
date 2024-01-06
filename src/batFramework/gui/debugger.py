from .label import Label
from typing import Self
import batFramework as bf
import pygame


def convert_to_int(*args):
    return [int(arg) for arg in args]



class Debugger(Label):
    def __init__(self) -> None:
        super().__init__("")
        self.static_data: dict = {}
        self.dynamic_data: dict = {}
        self.refresh_rate = 10
        self.refresh_counter : float = 0
        self.render_order = 99
        self.set_uid("debugger")

    def to_string_id(self) -> str:
        return "Debugger"

    def set_refresh_rate(self, value: int) -> Self:
        self.refresh_rate = value
        return self

    def add_data(self, key: str, data):
        self.static_data[key] = str(data)
        self.update_text()

    def add_dynamic_data(self, key: str, func) -> None:
        self.dynamic_data[key] = func
        self.update_text()

    def set_parent_scene(self, scene) -> Self:
        super().set_parent_scene(scene)
        self.update_text()
        return self

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
        if self.parent_scene.get_sharedVar("debugging_mode") not in [1,3]:
            self.set_visible(False)
            return
        self.set_visible(True)
        self.refresh_counter = self.refresh_counter + (dt * 60)
        if self.refresh_counter > self.refresh_rate:
            self.refresh_counter = 0
            self.update_text()


class BasicDebugger(Debugger):
    def __init__(self):
        super().__init__()

    def do_when_added(self):
        if not self.parent_scene or  not self.parent_scene.manager:
            print("Debugger could not link to the manager")
            return
        manager_link = self.parent_scene.manager
        parent_scene = self.parent_scene
        self.add_data("Resolution", 'x'.join(str(i) for i in bf.const.RESOLUTION))
        self.add_dynamic_data(
            "FPS", lambda: str(round(manager_link.get_fps()))
        )
        self.add_dynamic_data("Mouse", pygame.mouse.get_pos)
        self.add_dynamic_data(
            "World",
            lambda: convert_to_int(*parent_scene.camera.convert_screen_to_world(
                *pygame.mouse.get_pos())
            ),
        )
        self.add_dynamic_data(
            "Hud",
            lambda: convert_to_int(*parent_scene.hud_camera.convert_screen_to_world(
                *pygame.mouse.get_pos())
            ),
        )
        self.add_dynamic_data("W. Ent.",lambda : parent_scene.get_world_entity_count())
        self.add_dynamic_data("H. Ent.",lambda : parent_scene.get_hud_entity_count())
        

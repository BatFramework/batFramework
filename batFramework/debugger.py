import batFramework as bf
import pygame


class Debugger(bf.Label):
    def __init__(self, manager) -> None:
        super().__init__()
        self.manager: bf.Manager = manager
        self.refresh_rate = 0
        self._refresh_counter = 0
        self.dynamic_data = {}
        self.static_data = {}
        self.render_order = 99
        self.set_outline_color((20, 20, 20))
        # self.set_background_color((0,0,0,0))
        self.set_text_color("white")
        # self.set_padding((30,30))
        self.set_refresh_rate(20)
        self.add_dynamic_data("FPS", lambda: str(round(self.manager.get_fps())))
        self.add_dynamic_data("BLITS", lambda: str(self.parent_scene.blit_calls))
        self.set_visible(False)

    def set_refresh_rate(self, val: int):
        self.refresh_rate = val

    def update(self, dt: float):
        visible = self.manager._debugging == 1
        self.set_visible(visible)
        if not visible:
            return
        self._refresh_counter -= dt * 60
        if self._refresh_counter < 0:
            self._refresh_counter = self.refresh_rate
            self._refresh_debug_info()

    def add_dynamic_data(self, key, func):
        self.dynamic_data[key] = func

    def set_static_data(self, key, value):
        self.static_data[key] = value

    def _refresh_debug_info(self):
        lines = []
        lines.extend([f"{key}:{value}" for key, value in self.static_data.items()])
        lines.extend([f"{key}:{func()}" for key, func in self.dynamic_data.items()])
        debug_text = "\n".join(lines)
        self.set_text(debug_text)
        self.update_surface()  # Update the surface after modifying the text

import batFramework as bf
from utils import style


class CustomBaseScene(bf.Scene):
    def __init__(self, name, enable_alpha=True) -> None:
        super().__init__(name, enable_alpha)
        self.set_clear_color(bf.color.DARK_GB)

    def add_hud_entity(self, *entity):
        super().add_hud_entity(*entity)
        for e in entity:
            style.stylize(e)

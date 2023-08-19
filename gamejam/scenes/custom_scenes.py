import batFramework as bf
from utils import style
import pygame


class CustomBaseScene(bf.Scene):
    def __init__(self, name, enable_alpha=True) -> None:
        super().__init__(name, enable_alpha)
        self.set_clear_color(bf.color.DARK_GB)
        self.control = True

    def give_control(self):
        self.control = True

    def take_control(self):
        self.control = False
    def do_when_added(self):
        self.update(0.001)


    def add_hud_entity(self, *entity):
        super().add_hud_entity(*entity)
        for e in entity:
            style.stylize(e)






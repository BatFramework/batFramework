import batFramework as bf
from .shape import Shape
import pygame


class Frame(Shape):
    def __init__(self,width:float,height:float):
        super().__init__(width,height)
        self.set_debug_color("magenta")

    def to_string_id(self)->str:
        return "Frame"
    
    def children_modified(self)->None:
        # TODO CLEAN THIS UP
        if not self.children : return
        self.build_all()
        self.set_size(
            # *self.inflate_rect_by_padding(self.rect.unionall(list(c.rect for c in self.children))).size
            *self.inflate_rect_by_padding(self.children[0].rect.unionall(list(c.rect for c in self.children))).size
        )
        for c in self.children : 
            c.set_position(*c.rect.clamp(self.get_content_rect()).topleft)
        self.apply_constraints()
        super().children_modified()

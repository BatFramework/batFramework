# import batFramework as bf
from .shape import Shape
# import pygame


class Frame(Shape):
    def __init__(self,  size: tuple[float,float]=(0,0),fit_to_children:bool=True):
        self.fit_to_children = fit_to_children
        super().__init__(size)
        self.set_debug_color("magenta")
        
    def to_string_id(self) -> str:
        return "Frame"

    def _fit_to_children(self)->None:
        # TODO CLEAN THIS UP / Make it more reliable
        if not self.children: return
        children_rect = self.children[0].rect.unionall(list(c.rect for c in self.children))
        self.set_size(self.inflate_rect_by_padding(children_rect).size)
        self.rect.center = children_rect.center
        self.apply_all_constraints()
        
    def notify(self) -> None:
        super().notify()
        if self.fit_to_children:
            self._fit_to_children()

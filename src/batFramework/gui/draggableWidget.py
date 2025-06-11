from .interactiveWidget import InteractiveWidget
import batFramework as bf
import pygame


class DraggableWidget(InteractiveWidget):
    def __init__(self, *args, **kwargs) -> None:
        self.drag_start = None
        self.offset = None
        self.click_mask = [True,False,False,False,False]
        self.is_dragged : bool = False # the widget is following the mouse AND the mouse is in the widget
        self.is_dragged_outside : bool = False # the widget is following the mouse BUT the mouse is NOT in the widget
        super().__init__(*args, **kwargs)
    
    def set_click_mask(self,b1=0,b2=0,b3=0,b4=0,b5=0):
        self.click_mask = [b1,b2,b3,b4,b5]

    def on_click_down(self, button):
        super().on_click_down(button)
        return any(i==j and i== True for i,j in zip(self.is_clicked_down,self.click_mask))
    
    def do_on_drag(
        self, drag_start_pos: tuple[float, float], drag_end_pos: tuple[float, float]
    ) -> None:
        new_pos = drag_end_pos[0] - self.offset[0], drag_end_pos[1] - self.offset[1]
        if self.rect.topleft != new_pos:
            self.set_position(*new_pos)

    def update(self, dt: float):
        self.is_dragged_outside = any(i==j and i== True for i,j in zip(pygame.mouse.get_pressed(5),self.click_mask))
        self.is_dragged = any(i==j and i== True for i,j in zip(self.is_clicked_down,self.click_mask))

        if self.is_dragged and self.is_dragged_outside:
            x, y = self.parent_layer.camera.screen_to_world(pygame.mouse.get_pos())
            if self.drag_start == None:
                self.offset = x - self.rect.x, y - self.rect.y
                self.drag_start = x, y
            else:
                self.do_on_drag(self.drag_start, (x, y))
        else:
            self.drag_start = None
            self.offset = None
            self.is_clicked_down = [False]*5
        super().update(dt)

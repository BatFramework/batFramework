from .interactiveWidget import InteractiveWidget
import batFramework as bf
import pygame


class DraggableWidget(InteractiveWidget):
    def __init__(self, *args, **kwargs) -> None:

        self.drag_start = None
        self.offset = None
        super().__init__(*args, **kwargs)

    def on_click_down(self, button):
        if super().on_click_down(button)==False:
            return button == 1 # capture event
    
    def do_on_drag(
        self, drag_start: tuple[float, float], drag_end: tuple[float, float]
    ) -> None:
        self.set_position(drag_end[0] - self.offset[0], drag_end[1] - self.offset[1])


    def update(self, dt: float):
        if self.is_clicked_down and pygame.mouse.get_pressed(3)[0]:
            r = self.get_root()
            x, y = r.drawing_camera.screen_to_world(pygame.mouse.get_pos())
            if self.drag_start == None and self.is_clicked_down:
                self.offset = x - self.rect.x, y - self.rect.y
                self.drag_start = x, y
            else:
                self.do_on_drag(self.drag_start, (x, y))
                
        else:
            self.drag_start = None
            self.offset = None
            self.is_clicked_down = False
        super().update(dt)

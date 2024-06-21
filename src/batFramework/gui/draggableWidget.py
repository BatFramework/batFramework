from .interactiveWidget import InteractiveWidget
import batFramework as bf
import pygame


class DraggableWidget(InteractiveWidget):
    def __init__(self, *args, **kwargs) -> None:
        self.drag_action = bf.Action("dragging").add_mouse_control(1).set_holding()

        self.drag_start = None
        self.offset = None
        super().__init__(*args, **kwargs)

    def do_process_actions(self, event: pygame.Event) -> None:
        self.drag_action.process_event(event)

    def do_reset_actions(self) -> None:
        self.drag_action.reset()

    def do_on_drag(self,drag_start:tuple[float,float],drag_end: tuple[float,float])->None:
        self.set_position(drag_end[0]-self.offset[0],drag_end[1]-self.offset[1])

    def update(self, dt: float):
        if self.drag_action.active and self.is_clicked_down:
            r = self.get_root()
            x, y = r.drawing_camera.screen_to_world(pygame.mouse.get_pos())
            if self.drag_start == None and self.drag_action.active:
                self.offset = x-self.rect.x,y-self.rect.y
                self.drag_start = x,y
                return
            else:
                self.do_on_drag(self.drag_start,(x,y))
                return
        else:
            self.drag_start = None
            self.offset = None
            self.is_clicked_down = False
        super().update(dt)

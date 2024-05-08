from .interactiveWidget import InteractiveWidget
import batFramework as bf
import pygame

class DraggableWidget(InteractiveWidget):
    def __init__(self, *args, **kwargs) -> None:
        self.drag_action = bf.Action("dragging").add_mouse_control(1).set_holding()
        self.offset = None
        super().__init__(*args, **kwargs)

    def do_process_actions(self, event: pygame.Event) -> None:
        self.drag_action.process_event(event)

    def do_reset_actions(self) -> None:
        self.drag_action.reset()

    def update(self, dt: float):
        if self.drag_action.is_active()  and self.is_clicked_down:
            r = self.get_root()
            x,y = r.drawing_camera.convert_screen_to_world(*pygame.mouse.get_pos())
            if self.offset == None and self.drag_action.is_active():
                self.offset = x-self.rect.x,y-self.rect.y
                return
            else :
                self.set_position(x-self.offset[0],y-self.offset[1])
                return
        else:
            self.offset = None
        super().update(dt)


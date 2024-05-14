import batFramework as bf
from .interactiveWidget import InteractiveWidget
from .widget import Widget
import pygame


class Root(InteractiveWidget):
    def __init__(self,camera)->None:
        super().__init__()
        self.drawing_camera : bf.Camera = camera
        self.visible = False
        self.set_root()
        self.rect.size = pygame.display.get_surface().get_size()
        self.focused: InteractiveWidget |None= self
        self.hovered: Widget | None = self
        self.set_debug_color("yellow")
        self.set_render_order(999)
        self.disable_clip_to_parent()

    def to_string(self) -> str:
        return "Root"

    def to_string_id(self) -> str:
        return "Root"
        
    def get_focused(self) -> Widget | None:
        return self.focused

    def get_hovered(self) -> Widget | None:
        return self.hovered

    def clear_focused(self)->None:
        self.focus_on(None)

    def clear_hovered(self)->None:
        if isinstance(self.hovered,InteractiveWidget):   self.hovered.on_exit()
        self.hovered = None

    def focus_on(self, widget: InteractiveWidget|None) -> None:
        if widget and not widget.allow_focus_to_self():return
        if self.focused is not None:
            self.focused.on_lose_focus()
        if widget is None:
            self.focused = self
            return
        self.focused = widget
        self.focused.on_get_focus()

    def set_size(self, size : tuple[float,float], force: bool = False) -> "Root":
        if not force:
            return self
        self.rect.size = size
        self.build(apply_constraints=True)
        return self

    def build(self, apply_constraints: bool = False) -> None:
        if apply_constraints:
            self.apply_all_constraints()
        for child in self.children:
            child.build()

    def do_handle_event(self, event):
        # if event.type == pygame.VIDEORESIZE:
        #     self.set_size(event.w, event.h, force=True)
        #     return True
        if self.focused:
            if event.type == pygame.KEYDOWN:
                self.focused.on_key_down(event.key)
            if event.type == pygame.KEYUP:
                self.focused.on_key_up(event.key)
        if not self.hovered or not isinstance(self.hovered,InteractiveWidget) : return False
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.hovered.on_click_down(event.button)
        if event.type == pygame.MOUSEBUTTONUP:    
            self.hovered.on_click_up(event.button)            
        
        return False

    def get_root(self) -> "Root" :
        return self

    def do_on_click_down(self,button:int)->None:
        if button == 1 : self.clear_focused()

    def top_at(self, x: float|int, y: float|int) -> "None|Widget":
        if self.children:
            for child in reversed(self.children):
                r = child.top_at(x, y)
                if r is not None:
                    return r
        return self if self.rect.collidepoint(x,y) else None

    def update(self, dt: float) -> None:
        super().update(dt)
        old = self.hovered
        transposed = self.drawing_camera.screen_to_world(pygame.mouse.get_pos())
        self.hovered = (
            self.top_at(*transposed)
            if self.top_at(*transposed)
            else None
        )
        if old == self.hovered and isinstance(self.hovered,InteractiveWidget):
            self.hovered.on_mouse_motion(*transposed)
            return
        if old and isinstance(old,InteractiveWidget):    
            old.on_exit()
        if self.hovered and isinstance(self.hovered,InteractiveWidget) :
            self.hovered.on_enter()

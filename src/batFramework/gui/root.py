import batFramework as bf
from .interactiveWidget import InteractiveWidget
from .widget import Widget
import pygame


class Root(InteractiveWidget):
    def __init__(self,camera)->None:
        super().__init__()
        self.drawing_camera = camera
        self.surface = None
        self.set_root()
        self.rect.size = pygame.display.get_surface().get_size()
        self.focused: InteractiveWidget |None= self
        self.hovered: Widget | None = self
        self.set_debug_color("purple")

    def to_string(self) -> str:
        return "ROOT"

    def to_string_id(self) -> str:
        return "ROOT"
        
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
        if self.focused is not None:
            self.focused.on_lose_focus()
        if widget is None:
            self.focused = self
            return
        self.focused = widget
        self.focused.on_get_focus()

    def set_size(self, width: float, height: float, force: bool = False) -> "Root":
        if not force:
            return self
        self.rect.size = width, height
        self.build(apply_constraints=True)
        return self

    def build(self, apply_constraints: bool = False) -> None:
        if apply_constraints:
            self.apply_all_constraints()
        for child in self.children:
            child.build()

    def do_handle_event(self, event):
        if event.type == pygame.VIDEORESIZE:
            self.set_size(event.w, event.h, force=True)
            return True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered and isinstance(self.hovered,InteractiveWidget) :
                self.hovered.on_click_down(event.button)
        if event.type == pygame.MOUSEBUTTONUP:
            if self.hovered and isinstance(self.hovered,InteractiveWidget) :
                self.hovered.on_click_up(event.button)            

        return False

    def get_root(self) -> "Root" :
        return self

    def do_on_click_down(self,button:int)->None:
        if button == 1 : self.clear_focused()

    def update(self, dt: float) -> None:
        super().update(dt)
        old = self.hovered
        transposed = self.drawing_camera.convert_screen_to_world(*pygame.mouse.get_pos())
        self.hovered = (
            self.top_at(*transposed)
            if self.top_at(*transposed)
            else None
        )
        if old == self.hovered:
            return
        if old and isinstance(old,InteractiveWidget):    
            old.on_exit()
        if self.hovered and isinstance(self.hovered,InteractiveWidget) :
            self.hovered.on_enter()


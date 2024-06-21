from .widget import Widget
from typing import Self
from typing import TYPE_CHECKING
import pygame
from math import cos

if TYPE_CHECKING:
    from .container import Container
import batFramework as bf


class InteractiveWidget(Widget):
    def __init__(self, *args, **kwargs) -> None:
        self.is_focused: bool = False
        self.is_hovered: bool = False
        self.is_clicked_down: bool = False
        self.focused_index = 0
        self.focusable = True
        super().__init__(*args, **kwargs)

    def set_focusable(self, value: bool) -> Self:
        self.focusable = value
        return self

    def allow_focus_to_self(self) -> bool:
        return True

    def get_focus(self) -> bool:
        if self.focusable and ((r := self.get_root()) is not None):
            r.focus_on(self)
            if self.parent and isinstance(self.parent, InteractiveWidget):
                self.parent.set_focused_child(self)
            return True
        return False

    def lose_focus(self) -> bool:
        if self.is_focused and ((r := self.get_root()) is not None):
            r.focus_on(None)
            return True
        return False

    def on_get_focus(self) -> None:
        self.is_focused = True
        self.do_on_get_focus()

    def on_lose_focus(self) -> None:
        self.is_focused = False
        self.do_on_lose_focus()

    def on_key_down(self,key):
        if key == pygame.K_DOWN:
            self.focus_next_sibling()
        elif key == pygame.K_UP:
            self.focus_prev_sibling()
        else:
            self.do_on_key_down(key)

    def on_key_up(self, key):
        self.do_on_key_up(key)

    def do_on_key_down(self, key):
        pass

    def do_on_key_up(self, key):
        pass

    def do_on_get_focus(self) -> None:
        pass

    def do_on_lose_focus(self) -> None:
        pass

    def focus_next_sibling(self) -> None:
        if isinstance(self.parent, bf.Container):
            self.parent.focus_next_child()

    def focus_prev_sibling(self) -> None:
        if isinstance(self.parent, bf.Container):
            self.parent.focus_prev_child()

    def on_click_down(self, button: int) -> None:
        self.is_clicked_down = True
        self.do_on_click_down(button)

    def on_click_up(self, button: int) -> None:
        self.is_clicked_down = False
        self.do_on_click_up(button)

    def do_on_click_down(self, button: int) -> None:
        pass

    def do_on_click_up(self, button: int) -> None:
        pass

    def on_enter(self) -> None:
        self.is_hovered = True
        self.do_on_enter()

    def on_exit(self) -> None:
        self.is_hovered = False
        self.is_clicked_down = False
        self.do_on_exit()

    def do_on_enter(self) -> None:
        pass

    def do_on_exit(self) -> None:
        pass

    def on_mouse_motion(self, x, y) -> None:
        self.do_on_mouse_motion(x,y)

    def do_on_mouse_motion(self,x,y)->None:
        pass

    def set_focused_child(self, child: "InteractiveWidget"):
        pass

    def draw_focused(self, camera: bf.Camera) -> None: 
        delta = 4 + ((2*cos(pygame.time.get_ticks()/100)) //2) * 2
        pygame.draw.rect(
            camera.surface,
            "white",
            self.rect.move(-camera.rect.x,-camera.rect.y).inflate(delta,delta),1
        )

from .widget import Widget
from typing import Self
from typing import TYPE_CHECKING
import pygame
from math import cos,floor,ceil

if TYPE_CHECKING:
    from .container import Container
import batFramework as bf

def children_has_focus(widget)->bool:
    if isinstance(widget,InteractiveWidget) and widget.is_focused:
        return True
    for child in widget.children:
        if children_has_focus(child):
            return True
    return False


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
        return self.visible

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

    def set_parent(self, parent: Widget) -> Self:
        if parent is None and children_has_focus(self):
            self.get_root().clear_focused()
            # pass focus on

        return super().set_parent(parent)

    def on_get_focus(self) -> None:
        self.is_focused = True
        if isinstance(self.parent,bf.Container):
            self.parent.layout.scroll_to_widget(self) 
        self.do_on_get_focus()

    def on_lose_focus(self) -> None:
        self.is_focused = False
        self.do_on_lose_focus()

    def focus_next_tab(self, previous_widget):

        if previous_widget != self and self.visible:
            if (
                isinstance(self, InteractiveWidget)
                and not isinstance(self, bf.Container)
                and self.allow_focus_to_self()
            ):
                self.focus_next_sibling()
                return
            i_children = [
                c
                for c in self.children
                if isinstance(c, InteractiveWidget) and c.visible
            ]
            if i_children:
                index = i_children.index(previous_widget)
                if index < len(i_children) - 1:

                    i_children[index + 1].get_focus()
                    return

        if self.parent and isinstance(self.parent,InteractiveWidget):
            self.parent.focus_next_tab(self)

    def focus_prev_tab(self, previous_widget):
        if previous_widget != self and self.visible:
            if (
                isinstance(self, InteractiveWidget)
                and not isinstance(self, bf.Container)
                and self.allow_focus_to_self()
            ):
                self.get_focus()
                return
            i_children = [
                c
                for c in self.children
                if isinstance(c, InteractiveWidget) and c.visible
            ]

            if i_children:
                index = i_children.index(previous_widget)
                if index > 0:
                    i_children[index - 1].get_focus()
                    return

        if self.parent and isinstance(self.parent,InteractiveWidget):
            self.parent.focus_prev_tab(self)

    def on_key_down(self, key) -> bool:
        if key == pygame.K_TAB and self.parent:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:

                self.focus_prev_tab(self)
            else:
                self.focus_next_tab(self)
            return True
        else:

            return self.do_on_key_down(key)

        return False

    def on_key_up(self, key) -> bool:
        return self.do_on_key_up(key)

    def do_on_key_down(self, key) -> bool:
        return False

    def do_on_key_up(self, key) -> bool:
        return False

    def do_on_get_focus(self) -> None:
        pass

    def do_on_lose_focus(self) -> None:
        pass

    def on_click_down(self, button: int) -> bool:
        self.is_clicked_down = True
        return self.do_on_click_down(button)

    def on_click_up(self, button: int) -> bool:
        self.is_clicked_down = False
        return self.do_on_click_up(button)

    def do_on_click_down(self, button: int) -> bool:
        return False

    def do_on_click_up(self, button: int) -> bool:
        return False

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
        self.do_on_mouse_motion(x, y)

    def do_on_mouse_motion(self, x, y) -> None:
        pass

    def set_focused_child(self, child: "InteractiveWidget"):
        pass

    def draw_focused(self, camera: bf.Camera) -> None:

        proportion = 16
        surface = pygame.Surface(self.rect.inflate(proportion,proportion).size)
        surface.fill("black")

        delta = proportion*0.75 - int(proportion * cos(pygame.time.get_ticks() / 100) /4)
        delta = delta//2 * 2
        # Base rect centered in tmp surface
        base_rect = surface.get_frect()
        
        # Expanded white rectangle for border effect
        white_rect = base_rect.inflate(-delta,-delta)
        white_rect.center = base_rect.center
        pygame.draw.rect(surface, "white", white_rect, 2, *self.border_radius)
        
        # Black cutout rectangles to create the effect around the edges
        black_rect_1 = white_rect.copy()
        black_rect_1.w -= proportion
        black_rect_1.centerx = white_rect.centerx
        
        black_rect_2 = white_rect.copy()
        black_rect_2.h -= proportion
        black_rect_2.centery = white_rect.centery
        
        surface.fill("black", black_rect_1)
        surface.fill("black", black_rect_2)

        base_rect.center = self.rect.center

        surface.set_colorkey("black")
    
        # Blit the tmp surface onto the camera surface with adjusted position
        camera.surface.blit(
            surface,
            base_rect.move(-camera.rect.x, -camera.rect.y),
        )

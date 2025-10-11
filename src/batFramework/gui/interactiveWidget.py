from .widget import Widget
from typing import Self
import pygame
from math import cos
import batFramework as bf

def children_has_focus(widget)->bool:
    if isinstance(widget,InteractiveWidget) and widget.is_focused:
        return True
    for child in widget.children:
        if children_has_focus(child):
            return True
    return False


class InteractiveWidget(Widget):
    __focus_effect_cache = {}
    def __init__(self, *args, **kwargs) -> None:
        self.is_focused: bool = False
        self.is_hovered: bool = False
        self.is_clicked_down: list[bool] = [False]*5
        self.focused_index = 0
        self.click_pass_through : bool = False
        super().__init__(*args, **kwargs)


    def handle_event(self, event):
        if self.is_hovered:
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.is_clicked_down[event.button-1] = True
                self.on_click_down(event.button,event)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.is_clicked_down[event.button-1] = False
                self.on_click_up(event.button,event)

        if self.is_focused:
            if event.type == pygame.KEYDOWN:
                self.on_key_down(event.key,event)
            elif event.type == pygame.KEYUP:
                self.on_key_up(event.key,event)

    def set_click_pass_through(self,pass_through:bool)->Self:
        """
        # Allows mouse click events to pass through this widget to underlying widgets if True.
        """
        self.click_pass_through = pass_through
        return self


    def allow_focus_to_self(self) -> bool:
        return self.visible

    def get_focus(self) -> bool:
        if self.allow_focus_to_self() and ((r := self.get_root()) is not None):
            r.focus_on(self)
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

    def get_interactive_widgets(self):
        """Retrieve all interactive widgets in the tree, in depth-first order."""
        widgets = []
        stack = [self]
        while stack:
            widget = stack.pop()
            if isinstance(widget, InteractiveWidget) and widget.allow_focus_to_self():
                widgets.append(widget)
            stack.extend(reversed(widget.children))  # Add children in reverse for left-to-right traversal
        return widgets

    def find_next_widget(self, current):
        """Find the next interactive widget, considering parent and sibling relationships."""
        if current.is_root:
            return None  # Root has no parent

        if hasattr(current.parent, "layout"):
            siblings =  current.parent.get_interactive_children()
        else:
            siblings = current.parent.children 

        start_index = siblings.index(current)
        good_index = -1
        for i in range(start_index + 1, len(siblings)):
            sibling = siblings[i]
            if isinstance(sibling,InteractiveWidget) and  not(sibling is current) :
                if sibling.allow_focus_to_self():
                    good_index = i
                    break
        if good_index >= 0:
            # Not the last child, return the next sibling
            return siblings[good_index]
        else:
            # Current is the last child, move to parent's next sibling
            return self.find_next_widget(current.parent)

    def find_prev_widget(self, current : "Widget"):
        """Find the previous interactive widget, considering parent and sibling relationships."""
        if current.is_root:
            return None  # Root has no parent

        # siblings = [c for c in current.parent.children if isinstance(c,InteractiveWidget) and c.allow_focus_to_self()]
        if hasattr(current.parent, "layout"):
            siblings =  current.parent.get_interactive_children()
        else:
            siblings = current.parent.children 
        start_index = siblings.index(current)
        good_index = -1
        for i in range(start_index-1,-1,-1):
            sibling = siblings[i]
            if isinstance(sibling,InteractiveWidget) and  not(sibling is current) :
                if sibling.allow_focus_to_self():
                    good_index = i
                    break
        if good_index >= 0:
            # Not the first child, return the previous sibling
            return siblings[good_index]
        else:
            # Current is the first child, move to parent's previous sibling
            return self.find_prev_widget(current.parent)

    def focus_next_tab(self, previous_widget):
        """Focus the next interactive widget."""
        if previous_widget:
            next_widget = self.find_next_widget(previous_widget)
            if next_widget:
                next_widget.get_focus()

    def focus_prev_tab(self, previous_widget):
        """Focus the previous interactive widget."""
        if previous_widget:
            prev_widget = self.find_prev_widget(previous_widget)
            if prev_widget:
                prev_widget.get_focus()


    
    def on_key_down(self, key,event) -> None:
        self.do_on_key_down(key,event)

    def on_key_up(self, key,event) -> None:
        self.do_on_key_up(key,event)

    def on_click_down(self, button: int,event=None) -> None:
        if not self.click_pass_through:
            event.consumed = True
        self.do_on_click_down(button,event)

    def on_click_up(self, button: int,event=None) -> None:
        if not self.click_pass_through:
            event.consumed = True
        self.do_on_click_up(button,event)

    def on_get_focus(self) -> None:
        self.is_focused = True
        if isinstance(self.parent,bf.gui.InteractiveWidget):
            self.parent.set_focused_child(self)
        self.do_on_get_focus()

    def on_lose_focus(self) -> None:
        self.is_focused = False
        self.do_on_lose_focus()

    def do_on_get_focus(self) -> None:
        pass

    def do_on_lose_focus(self) -> None:
        pass

    def do_on_key_down(self, key,event) -> None:
        return

    def do_on_key_up(self, key,event) -> None:
        return

    def do_on_click_down(self, button: int,event=None) -> None:
        return 

    def do_on_click_up(self, button: int,event=None) -> None:
        return 

    def on_enter(self) -> None:
        self.is_hovered = True
        self.do_on_enter()

    def on_exit(self) -> None:
        self.is_hovered = False
        self.is_clicked_down = [False]*5
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
        if isinstance(self,bf.gui.Shape):
            prop = 8
            pulse = int(prop * 0.75 - (prop * cos(pygame.time.get_ticks() / 100) / 4))
            delta = (pulse // 2) * 2  # ensure even

            # Get rect in screen space, inflated for visual effect
            screen_rect = camera.world_to_screen(self.rect.inflate(prop+self.outline_width, prop+self.outline_width))

            # Shrink for inner pulsing border
            inner = screen_rect.inflate(-delta, -delta)
            inner.topleft = 0,0
            inner.w = round(inner.w)
            inner.h = round(inner.h)

            surface = InteractiveWidget.__focus_effect_cache.get(inner.size)
            if surface is None:
                surface = pygame.Surface(inner.size)
                InteractiveWidget.__focus_effect_cache[inner.size] = surface

            surface.set_colorkey((0,0,0))
            pygame.draw.rect(surface, "white", inner, 2, *self.border_radius)
            pygame.draw.rect(surface, "black", inner.inflate(-1 * min(16,inner.w*0.75),0), 2)
            pygame.draw.rect(surface, "black", inner.inflate(0,-1 * min(16,inner.h*0.75)), 2)
            inner.center = screen_rect.center
            camera.surface.blit(surface,inner)


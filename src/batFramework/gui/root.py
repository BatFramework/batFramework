import batFramework as bf
from .interactiveWidget import InteractiveWidget
from .widget import Widget
import pygame
from typing import Self
import sys


class Root(InteractiveWidget):
    def __init__(self, camera) -> None:
        super().__init__()
        self.is_root = True
        self.drawing_camera: bf.Camera = camera
        self.visible = False
        self.rect.size = pygame.display.get_surface().get_size()
        self.focused: InteractiveWidget | None = self
        self.hovered: Widget | None = self
        self.show_tooltip : bool = True
        self.tooltip = bf.gui.Label("")  # Tooltip label
        self.tooltip.set_visible(False)  # Initially hidden
        self.tooltip.set_color(bf.color.CLOUD)  # Background color for the tooltip
        self.tooltip.set_text_color(bf.color.LIGHT_GRAY)  # Text color for the tooltip
        self.add(self.tooltip)  # Add tooltip to the root
        self.tooltip.set_border_radius((2,0,2,2))
        self.tooltip.set_render_order(sys.maxsize)
        self.tooltip.top_at = lambda *args : None
        self.set_debug_color("yellow")
        self.clip_children = False

    def toogle_tooltip(self,value:bool)->Self:
        self.show_tooltip = value
        return self
    
    def __str__(self) -> str:
        return "Root"
    
    def to_ascii_tree(self)->str:
        def f(w,depth):
            tmp = '\n'.join(f(c,depth+1) for c in w.children) if w.children else None
            return '\t'*depth + str(w) + (("\n"+tmp) if tmp else "")
        return f(self,0)

    def set_parent_scene(self, parent_scene: bf.Scene) -> Self:
        bf.gui.StyleManager().register_widget(self)
        return super().set_parent_scene(parent_scene)

    def get_focused(self) -> Widget | None:
        return self.focused

    def get_hovered(self) -> Widget | None:
        return self.hovered

    def clear_focused(self) -> None:
        self.focus_on(None)

    def clear_hovered(self) -> None:
        if isinstance(self.hovered, InteractiveWidget):
            self.hovered.on_exit()
        self.hovered = None

    def get_debug_outlines(self):
        yield (self.rect, self.debug_color)
        for child in self.children:
            yield from child.get_debug_outlines()

    def focus_on(self, widget: InteractiveWidget | None) -> None:
        if widget == self.focused:
            return
        if widget and not widget.allow_focus_to_self():
            return
        if self.focused is not None:
            self.focused.on_lose_focus()
        if widget is None:
            self.focused = self
            return
        self.focused = widget
        self.focused.on_get_focus()

    def get_by_tags(self, *tags) -> list[Widget]:
        res = []

        def getter(w: Widget):
            nonlocal res
            if any(t in w.tags for t in tags):
                res.append(w)

        self.visit(getter)
        return res

    def focus_next_tab(self, widget):
        return

    def focus_prev_tab(self, widget):
        return

    def get_by_uid(self, uid: int) -> "Widget":
        def helper(w: "Widget", uid: int) -> "Widget":
            if w.uid == uid:
                return w
            for child in w.children:
                res = helper(child, uid)
                if res is not None:
                    return res
            return None

        return helper(self, uid)

    def set_size(self, size: tuple[float, float], force: bool = False) -> "Root":
        if not force:
            return self
        self.rect.size = size
        self.dirty_shape = True
        self.dirty_constraints = True
        return self

    def process_event(self,event):
        if event.consumed : return
        self.do_handle_event_early(event)
        if event.consumed : return
        super().process_event(event)
        
    def do_handle_event_early(self, event):
        if event.type == pygame.VIDEORESIZE:
            self.set_size((event.w,event.h),force=True)
        if self.focused:
            if event.type == pygame.KEYDOWN:
                if self.focused.on_key_down(event.key):
                    event.consumed = True
            elif event.type == pygame.KEYUP:
                if self.focused.on_key_up(event.key):
                    event.consumed = True

        if not self.hovered or (not isinstance(self.hovered, InteractiveWidget)):
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered.on_click_down(event.button):
                event.consumed = True

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.hovered.on_click_up(event.button):
                event.consumed = True
    def do_on_click_down(self, button: int) -> None:
        if button == 1:
            self.clear_focused()

    def top_at(self, x: float | int, y: float | int) -> "None|Widget":
        if self.children:
            for child in reversed(self.children):
                r = child.top_at(x, y)
                if r is not None:
                    return r
        return self if self.rect.collidepoint(x, y) else None

    def update(self, dt: float) -> None:
        super().update(dt)
        old = self.hovered
        transposed = self.drawing_camera.screen_to_world(pygame.mouse.get_pos())
        self.hovered = self.top_at(*transposed) if self.top_at(*transposed) else None

        # Tooltip logic
        if self.hovered and self.hovered.tooltip_text is not None:
            # Show tooltip if the hovered widget has a tooltip
            self.tooltip.set_text(self.hovered.tooltip_text)
            self.tooltip.set_visible(True)
            mouse_pos = pygame.mouse.get_pos()
            self.tooltip.set_position(*self.drawing_camera.world_to_screen_point(mouse_pos))  # Offset tooltip slightly
        else:
            # Hide tooltip if no widget with a tooltip is hovered
            self.tooltip.set_visible(False)

        if old == self.hovered and isinstance(self.hovered, InteractiveWidget):
            self.hovered.on_mouse_motion(*transposed)
            return
        if old and isinstance(old, InteractiveWidget):
            old.on_exit()
        if self.hovered and isinstance(self.hovered, InteractiveWidget):
            self.hovered.on_enter()

    def apply_updates(self):
        if any(child.dirty_shape for child in self.children):
            self.dirty_shape = True  # Mark layout as dirty if any child changed size

        if self.dirty_shape:
            for child in self.children:
                child.dirty_constraints = True
            for child in self.children:
                child.apply_updates()
            self.dirty_shape = False

    def draw(self, camera: bf.Camera) -> None:
        super().draw(camera)
        if (
            self.parent_scene
            and self.parent_scene.active
            and self.focused
            and self.focused != self
        ):
            clip:bool =self.focused.parent and self.focused.parent.clip_children
            if clip:
                old_clip = camera.surface.get_clip()
                camera.surface.set_clip(camera.world_to_screen(self.focused.parent.rect))    
            self.focused.draw_focused(camera)
            if clip:
                camera.surface.set_clip(old_clip)
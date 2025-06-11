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
        self.clip_children = False
        self.set_debug_color("yellow")

        self.show_tooltip : bool = True
        self.tooltip = bf.gui.ToolTip("").set_visible(False)
        self.add(self.tooltip)

    def toggle_tooltip(self,value:bool)->Self:
        self.show_tooltip = value
        return self
    
    def __str__(self) -> str:
        return "Root"
    
    def to_ascii_tree(self) -> str:
        def f(w, depth):
            prefix = " " * (depth * 4) + ("└── " if depth > 0 else "")
            children = "\n".join(f(c, depth + 1) for c in w.children) if w.children else ""
            return f"{prefix}{str(w)}\n{children}"
        return f(self, 0)

    def set_parent_scene(self, parent_scene: bf.Scene) -> Self:
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
        self.dirty_size_constraints = True
        return self

    def process_event(self,event):
        if not event.consumed : self.do_handle_event_early(event)
        if not event.consumed : super().process_event(event)
        
    def do_handle_event_early(self, event):
        if event.type == pygame.VIDEORESIZE and not pygame.SCALED & bf.const.FLAGS:
            self.set_size((event.w,event.h),force=True)
        if self.focused:
            if event.type == pygame.KEYDOWN:
                event.consumed = self.focused.on_key_down(event.key)
                if not event.consumed : 
                    event.consumed = self._handle_alt_tab(event.key)
            elif event.type == pygame.KEYUP:
                event.consumed = self.focused.on_key_up(event.key)

        if not self.hovered or (not isinstance(self.hovered, InteractiveWidget)):
            event.consumed = True
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            event.consumed = self.hovered.on_click_down(event.button)

        elif event.type == pygame.MOUSEBUTTONUP:
            event.consumed = self.hovered.on_click_up(event.button)
            
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
        self.update_tree()

        mouse_screen = pygame.mouse.get_pos()
        mouse_world = self.drawing_camera.screen_to_world(mouse_screen)
        prev_hovered = self.hovered
        self.hovered = self.top_at(*mouse_world) or None

        # Tooltip logic
        if self.hovered and self.hovered.tooltip_text:
            self.tooltip.set_text(self.hovered.tooltip_text)

            tooltip_size = self.tooltip.get_min_required_size()
            screen_w, screen_h = self.drawing_camera.rect.size
            tooltip_x, tooltip_y = self.drawing_camera.world_to_screen_point(mouse_world)

            tooltip_x = min(tooltip_x, screen_w - tooltip_size[0])
            tooltip_y = min(tooltip_y, screen_h - tooltip_size[1])
            tooltip_x = max(0, tooltip_x)
            tooltip_y = max(0, tooltip_y)

            self.tooltip.set_position(tooltip_x, tooltip_y)
            self.tooltip.fade_in()
        else:
            self.tooltip.fade_out()

        if self.hovered == prev_hovered:
            if isinstance(self.hovered, InteractiveWidget):
                self.hovered.on_mouse_motion(*mouse_world)
            return

        if isinstance(prev_hovered, InteractiveWidget):
            prev_hovered.on_exit()
        if isinstance(self.hovered, InteractiveWidget):
            self.hovered.on_enter()


    def _handle_alt_tab(self,key):
        if self.focused is None:
            return False
        if key != pygame.K_TAB:
            return False
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            self.focused.focus_prev_tab(self.focused)
        else:
            self.focused.focus_next_tab(self.focused)
        return True

    def update_tree(self):
        # print("START updating tree")
        self.apply_updates("pre")
        self.apply_updates("post")

        self.apply_updates("pre")
        self.apply_updates("post")

        # print("END updating tree")

    def apply_pre_updates(self):
        return 

    def apply_post_updates(self, skip_draw = False):
        return

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
            if clip:
                camera.surface.set_clip(old_clip)
            self.focused.draw_focused(camera)   
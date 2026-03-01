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

        self.show_tooltip: bool = True
        self.tooltip = bf.gui.ToolTip("").set_visible(False)
        self.add(self.tooltip)
        self.set_click_pass_through(True)

        # Track what widget is currently showing tooltip
        self._tooltip_target: Widget | None = None

    def set_show_tooltip(self, value: bool) -> Self:
        self.show_tooltip = value
        return self

    def __str__(self) -> str:
        return "Root"

    def to_ascii_tree(self) -> str:
        def f(w: Widget, depth):
            prefix = " " * (depth * 4) + ("L__ " if depth > 0 else "")
            children = (
                "\n".join(f(c, depth + 1) for c in w.children) if w.children else ""
            )
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

    def focus_on(self, widget: InteractiveWidget | None, focus_area : pygame.Rect=None) -> None:
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
        self.focused.on_get_focus(focus_area)

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

    def process_event(self, event):
        if not event.consumed:
            self.handle_event_early(event)
        super().process_event(event)

    def handle_event_early(self, event):
        if event.type == pygame.VIDEORESIZE and not pygame.SCALED & bf.const.FLAGS:
            self.set_size((event.w, event.h), force=True)
        return

    def handle_event(self, event):
        super().handle_event(event)
        if not event.consumed:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                self.tab_focus(event)

    def tab_focus(self, event=None):
        if self.focused is None:
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            self.focused.focus_prev_tab(self.focused)
        else:
            self.focused.focus_next_tab(self.focused)
        if event:
            event.consumed = True

    def on_click_down(self, button: int, event) -> None:
        if button == 1:
            self.clear_focused()
        super().on_click_down(button, event)

    def top_at(self, x: float | int, y: float | int) -> "None|Widget":
        for child in reversed(self.children):
            r = child.top_at(x, y)
            if r is not None:
                return r
        return self if self.rect.collidepoint(x, y) else None

    def update(self, dt: float) -> None:
        super().update(dt)
        self.update_tree()

        mouse_world = self.drawing_camera.get_mouse_pos()
        prev_hovered = self.hovered
        self.hovered = self.top_at(*mouse_world)

        # Tooltip logic: only trigger fade when target changes
        current_tooltip_widget = (
            self.hovered if (self.hovered and self.hovered.tooltip_text) else None
        )
        if current_tooltip_widget:
            self.tooltip.set_text(current_tooltip_widget.tooltip_text)
        if current_tooltip_widget != self._tooltip_target:
            # Tooltip target changed
            if current_tooltip_widget and self.show_tooltip:
                # Start showing tooltip for new target

                self.tooltip.fade_in()
            else:
                # Hide tooltip (either no target or tooltip disabled)
                self.tooltip.fade_out()

            self._tooltip_target = current_tooltip_widget

        # Position tooltip
        if self.tooltip.visible:
            offset = 2
            mouse_x, mouse_y = mouse_world
            tooltip_rect = pygame.FRect(mouse_x, mouse_y,*self.tooltip.get_min_required_size())
            screen_rect = pygame.Rect(0,0,*bf.const.RESOLUTION)

            screen_rect = self.drawing_camera.world_to_screen(screen_rect).inflate(10,10) # TODO : tooltip rect margin is hardcoded :/
            if tooltip_rect.right + offset <= screen_rect.right:
                tooltip_rect.move_ip(offset,0)
            else:
                tooltip_rect.move_ip(-tooltip_rect.w - offset,0)

            if tooltip_rect.bottom + offset <= screen_rect.bottom:
                tooltip_rect.move_ip(0,offset)
            else:
                tooltip_rect.move_ip(0,-tooltip_rect.h - offset)            
            
            self.tooltip.set_position(tooltip_rect.x, tooltip_rect.y)

        # Handle hover state changes
        if self.hovered == prev_hovered:
            if isinstance(self.hovered, InteractiveWidget):
                self.hovered.on_mouse_motion(*mouse_world)
            return

        if isinstance(prev_hovered, InteractiveWidget):
            prev_hovered.on_exit()
        if isinstance(self.hovered, InteractiveWidget):
            self.hovered.on_enter()

    def update_tree(self):
        # 1st pass
        self.apply_updates("pre")
        self.apply_updates("post")
        # 2nd pass
        # self.apply_updates("pre")
        # self.apply_updates("post")

    def apply_pre_updates(self):
        return

    def apply_post_updates(self, skip_draw=False):
        return

    def draw(self, camera: bf.Camera) -> None:
        if self.clip_children:
            new_clip = camera.world_to_screen(self.get_inner_rect())
            old_clip = camera.surface.get_clip()
            camera.surface.set_clip(new_clip)

        # Draw each child widget, sorted by render order
        for child in [c for c in self.children if c != self.tooltip]:
            if (not self.clip_children) or (
                child.rect.colliderect(self.rect) or not child.rect
            ):
                child.draw(camera)
        if self.clip_children:
            camera.surface.set_clip(old_clip)

        if self.focused != self and (not self.focused is None):
            old_clip = camera.surface.get_clip()
            # set clip to focused widget's parent
            camera.surface.set_clip(self.focused.parent.rect)
            self.focused.draw_focused(camera)
            camera.surface.set_clip(old_clip)

        self.tooltip.draw(camera)

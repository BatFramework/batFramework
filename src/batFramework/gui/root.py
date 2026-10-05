import batFramework as bf
from .interactiveWidget import InteractiveWidget
from .widget import Widget
from .guiUtils import fit_rect, inset_rect
import pygame
from typing import Self, Callable


class Root(InteractiveWidget):
    is_focus_scope = True

    def __init__(self, camera: bf.Camera | None = None) -> None:
        super().__init__()
        self._layers: dict[bf.gui.GuiLayer, list[Widget]] = {
            l: [] for l in bf.gui.GuiLayer if l != bf.gui.GuiLayer.NORMAL
        }
        self._popup_layouts: dict[Widget, Callable[[pygame.FRect], None]] = {}
        self.is_root = True
        self._default_camera: bf.Camera | None = camera  # used while not in a scene
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


    @property
    def drawing_camera(self) -> bf.Camera:
        """Camera the gui is drawn with (the camera of the root's layer in the scene)"""
        return self.get_camera() or self._default_camera

    def set_show_tooltip(self, value: bool) -> Self:
        self.show_tooltip = value
        if not value:
            self.tooltip.set_target(None)
        return self

    def __str__(self) -> str:
        return "Root"

    def attach_to_layer(self, widget: Widget, layer: bf.gui.GuiLayer,
                        layout_callback: Callable[[pygame.FRect], None] | None = None) -> None:
        if layer == bf.gui.GuiLayer.NORMAL:
            return # NORMAL layer is for regular child widgets, not layered ones; ignore layer assignment for NORMAL
        if widget.parent is not None and widget.parent is not self :
            widget.parent.remove(widget)
        if widget not in self.children:
            self.add(widget)
        
        widget.gui_layer = layer
        for layer_widgets in self._layers.values():
            if widget in layer_widgets:
                layer_widgets.remove(widget)
        self._layers[layer].append(widget)
        self._popup_layouts.pop(widget, None)
        if layout_callback is not None:
            self._popup_layouts[widget] = layout_callback

    def detach_from_layer(self, widget: Widget) -> None:
        self._popup_layouts.pop(widget, None)
        for layer_widgets in self._layers.values():
            if widget in layer_widgets:
                layer_widgets.remove(widget)
        if widget.parent is self:
            self.remove(widget)

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
        self.tooltip.set_target(None)

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
        self.dirty_surface = True
        self.mark_shape_dirty()
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
        if button == 1 and not getattr(event, "synthetic_capture", False):
            self.clear_focused()
        super().on_click_down(button, event)

    def top_at(self, x: float | int, y: float | int) -> "None|Widget":
        layered = {w for widgets in self._layers.values() for w in widgets}
        for layer in sorted(self._layers, reverse=True):
            for widget in reversed(self._layers[layer]):
                if widget.visible and (hit := widget.top_at(x, y)) is not None:
                    return hit
        for child in reversed(self.children):
            if child in layered:
                continue
            r = child.top_at(x, y)
            if r is not None:
                return r
        return self if self.rect.collidepoint(x, y) else None

    def update(self, dt: float) -> None:
        super().update(dt)
        self.update_tree()

    def _update_hover(self, mouse_world):
        """Hit-test the normal UI after its final rectangles have been assigned."""
        prev_hovered = self.hovered
        self.hovered = self.top_at(*mouse_world)

        # Handle hover state changes
        if self.hovered == prev_hovered:
            if isinstance(self.hovered, InteractiveWidget):
                self.hovered.on_mouse_motion(*mouse_world)
            return
        if isinstance(prev_hovered, InteractiveWidget):
            prev_hovered.on_exit()
        if isinstance(self.hovered, InteractiveWidget):
            self.hovered.on_enter()

    def measure(self, available_size):
        super().measure(available_size)
        self.desired_size = self.available_size
        return self.desired_size

    def measure_override(self, available_size):
        # The tooltip has its own bounded layout pass after hover is resolved.
        for child in self.children:
            if child is not self.tooltip and child not in self._popup_layouts:
                child.measure(available_size)
        return self.get_min_required_size()

    def arrange_override(self):
        self.arrange_children(exclude=(self.tooltip, *self._popup_layouts))

    @staticmethod
    def _place_tooltip(size, mouse_world, bounds, gap, margin=0):
        """Pure placement: prefer down/right, flip at edges, then clamp."""
        x, y = mouse_world
        safe_bounds = inset_rect(bounds, margin)
        rect = pygame.FRect(x + gap, y + gap, *size)
        if rect.right > safe_bounds.right:
            rect.x = x - gap - rect.width
        if rect.bottom > safe_bounds.bottom:
            rect.y = y - gap - rect.height
        return fit_rect(rect, bounds, rect.topleft, margin)

    def _layout_tooltip(self, mouse_world, viewport):
        if not self.tooltip.visible:
            return
        # Keep all geometry in GUI world coordinates, including camera bounds.
        margin = self.tooltip.screen_margin
        bounds = inset_rect(viewport, margin)
        available = (min(self.tooltip.max_width, bounds.width), bounds.height)
        desired = self.tooltip.measure(available)
        gap = max(0, 2 + 2 * self.tooltip.offset_scale)
        rect = self._place_tooltip(desired, mouse_world, viewport, gap, margin)
        self.tooltip.arrange(rect)

    def update_tree(self):
        self.measure(self.rect.size)
        self.arrange(self.rect)
        camera = self.drawing_camera
        viewport = camera.world_rect if camera is not None else self.rect
        # Anchors now have final rectangles. Popups negotiate their bounded
        # allocations before hover resolution and before the tree is painted.
        for popup, layout in tuple(self._popup_layouts.items()):
            if popup.visible:
                layout(viewport.copy())
        if camera is not None:
            mouse_world = camera.get_mouse_pos()
            self._update_hover(mouse_world)
            target = self.hovered if (self.show_tooltip and self.hovered
                                      and self.hovered.tooltip_text) else None
            self.tooltip.set_target(target)
            self._layout_tooltip(mouse_world, camera.world_rect)
        self.paint_tree()

    def needs_paint(self) -> bool:
        # Root owns layout and layers, but has no visual surface of its own.
        return False

    def draw(self, camera):
        layered = {w for layer_widgets in self._layers.values() for w in layer_widgets}
        for child in self.children:
            if child in layered: # skip widgets that are drawn in layers after the main pass
                continue
            child.draw(camera)

        if self.focused is not self and self.focused \
            is not None and self.focused.parent is not None \
                and self.focused.draw_focused is not None:
            old_clip = camera.surface.get_clip()
            camera.surface.set_clip(self.focused.parent.rect)
            self.focused.draw_focused(camera)
            camera.surface.set_clip(old_clip)

        for layer in sorted(self._layers.keys()):
            for w in self._layers[layer]:
                w.draw(camera)

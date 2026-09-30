import pygame
import batFramework as bf
import logging
from typing import Self
from .container import Container
from .widget import Widget
from .layout import Layout
from .interactiveWidget import InteractiveWidget
from .slider import SliderMeter
from .syncedVar import SyncedVar

logger = logging.getLogger(__name__)

class _ScrollBar(SliderMeter):
    """A slider with a proportional thumb and container-owned wheel handling."""

    def __init__(self, axis: int):
        self.scroll_axis = axis
        self.viewport_fraction = 1.0
        self.minimum_thumb_length = 12
        super().__init__(synced_var=SyncedVar(0.0))
        self.set_direction(bf.direction.DOWN if axis else bf.direction.RIGHT)
        self.set_autoresize(False).set_color((0, 0, 0, 40))
        self.content.set_alpha(0)

    def get_min_required_size(self):
        # The container assigns the rail, independently of the content's size.
        return (0, 0)

    def get_handle_size(self, available_size):
        size = list(available_size)
        axis = self.scroll_axis
        size[axis] = min(size[axis], max(self.minimum_thumb_length,
                                        size[axis] * self.viewport_fraction))
        return tuple(size)

    def allow_focus_to_self(self):
        return False

    def ask_focus(self, focus_area=None):
        # Scrolling must preserve the focused content widget.
        return True

    def handle_event(self, event):
        # Wheel events bubble to the container, which uses pixel scroll speed.
        if not self.visible or not self.is_enabled:
            return
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP) and event.button in (4, 5):
            if self.is_hovered:
                event.consumed = True
            return
        InteractiveWidget.handle_event(self, event)


class ScrollingContainer(Container):
    """Measure overflow, allocate a viewport, then arrange content and sliders."""

    def __init__(self, layout: Layout = None, *children: Widget) -> None:
        self._scrollbar_thickness = 8
        self._scroll_speed = 20.0
        self._scroll_x_enabled = True
        self._scroll_y_enabled = True
        self._scroll_track_x_gap = 4
        self._scroll_track_y_gap = 4
        self._bars = (False, False)  # horizontal, vertical; committed by arrange
        self._measured_base_size = None
        self._measured_bars = self._bars
        self._syncing_scrollbars = False

        # Keep the public styling references; each handle belongs to its slider.
        self.h_track = _ScrollBar(0)
        self.v_track = _ScrollBar(1)
        self.h_handle = self.h_track.handle
        self.v_handle = self.v_track.handle
        self._scrollbar_widgets = (self.h_track, self.v_track)
        super().__init__(layout, *children)
        for axis, track in enumerate(self._scrollbar_widgets):
            self.add(track.set_visible(False))
            track.handle.set_visible(False)
            track.set_draw_order(999)
            track.synced_var.bind(self, lambda value, axis=axis: self._scroll_from_bar(axis, value))
        self.set_clip_children(True)
        self.set_debug_color("yellow")

    def __str__(self):
        return f"ScrollingContainer({self.uid},{len(self.get_layout_children())})"

    def set_scrollbar_thickness(self, thickness: float) -> Self:
        self._scrollbar_thickness = max(2, thickness)
        self._measured_base_size = None
        self.dirty_surface = True
        return self

    def set_scrollbar_x_gap(self, gap: int) -> Self:
        self._scroll_track_x_gap = max(0, gap)
        self._measured_base_size = None
        self.dirty_surface = True
        return self

    def set_scrollbar_y_gap(self, gap: int) -> Self:
        self._scroll_track_y_gap = max(0, gap)
        self._measured_base_size = None
        self.dirty_surface = True
        return self

    def set_scroll_speed(self, speed: float) -> Self:
        self._scroll_speed = max(1.0, speed)
        return self

    def set_scroll_x_enabled(self, enabled: bool) -> Self:
        self._scroll_x_enabled = enabled
        self._measured_base_size = None
        self.clamp_scroll()
        self.dirty_surface = True
        return self

    def set_scroll_y_enabled(self, enabled: bool) -> Self:
        self._scroll_y_enabled = enabled
        self._measured_base_size = None
        self.clamp_scroll()
        self.dirty_surface = True
        return self

    def get_layout_children(self):
        return [child for child in self.children if child not in self._scrollbar_widgets]

    def clear_children(self) -> None:
        self.remove(*self.get_layout_children())
        self.reset_scroll()

    def _reservations(self, bars):
        return (self._scrollbar_thickness + self._scroll_track_y_gap if bars[1] else 0,
                self._scrollbar_thickness + self._scroll_track_x_gap if bars[0] else 0)

    def _viewport_size(self, base_size, bars):
        reserved = self._reservations(bars)
        return tuple(max(0, size - gap) for size, gap in zip(base_size, reserved))

    def get_inner_rect(self):
        rect = super().get_inner_rect()
        rect.size = self._viewport_size(rect.size, self._bars)
        return rect

    def get_local_inner_rect(self):
        return self.get_inner_rect().move(-self.rect.x, -self.rect.y)

    def get_inner_width(self):
        return self.get_inner_rect().width

    def get_inner_height(self):
        return self.get_inner_rect().height

    def get_inner_right(self):
        return self.get_inner_rect().right

    def get_inner_bottom(self):
        return self.get_inner_rect().bottom

    def _scroll_limits(self):
        viewport = self.get_inner_rect().size
        content = self.layout.children_rect.size
        return tuple(max(0, content[i] - viewport[i]) if enabled else 0
                     for i, enabled in enumerate((self._scroll_x_enabled, self._scroll_y_enabled)))

    def clamp_scroll(self) -> Self:
        for axis, limit in enumerate(self._scroll_limits()):
            self.scroll[axis] = max(0, min(self.scroll[axis], limit))
        return self

    def _scroll_from_bar(self, axis, ratio):
        if not self._syncing_scrollbars:
            scroll = self.scroll.copy()
            scroll[axis] = ratio * self._scroll_limits()[axis]
            self.set_scroll(scroll)

    def get_layout_available_size(self, available_size):
        return (float("inf") if self._scroll_x_enabled else available_size[0],
                float("inf") if self._scroll_y_enabled else available_size[1])

    def _measure_viewport(self, base_size):
        # Each iteration can add a bar. Remeasure bounded axes when a bar
        # consumes space, so wrapped content reports its new height immediately.
        bars = (False, False)
        enabled = (self._scroll_x_enabled, self._scroll_y_enabled)
        for _ in range(3):
            viewport = self._viewport_size(base_size, bars)
            content = self.layout.measure(self.get_layout_available_size(viewport))
            needed = tuple(bars[i] or (enabled[i] and content[i] > viewport[i]) for i in (0, 1))
            if needed == bars:
                break
            bars = needed
        self._measured_base_size = tuple(base_size)
        self._measured_bars = bars
        return content, bars

    def _outer_size(self, content, bars):
        reserved = self._reservations(bars)
        return (content[0] + self.padding[0] + self.padding[2] + reserved[0],
                content[1] + self.padding[1] + self.padding[3] + self.relief + reserved[1])

    def get_min_required_size(self):
        return self.compute_min_size(self._outer_size(self.layout.get_raw_size(), self._bars))

    def measure_override(self, available_size):
        content, bars = self._measure_viewport(available_size)
        for track in self._scrollbar_widgets:
            track.measure(available_size)
        return self._outer_size(content, bars)

    def arrange_override(self):
        base = super().get_inner_rect()
        # An allocation can differ from the offer. Resolve that viewport before
        # assigning any child rectangles; never arrange content speculatively.
        if base.size != self._measured_base_size:
            self._measure_viewport(base.size)
        self._bars = self._measured_bars
        self.layout.arrange()
        viewport = self.get_inner_rect()
        limits = self._scroll_limits()
        self._syncing_scrollbars = True
        try:
            for axis, track in enumerate(self._scrollbar_widgets):
                visible = self._bars[axis]
                track.set_visible(visible)
                track.handle.set_visible(visible)
                content_length = self.layout.children_rect.size[axis]
                track.viewport_fraction = min(1, viewport.size[axis] / content_length) if content_length else 1
                track.minimum_thumb_length = self._reservations(self._bars)[1 - axis]
                track.set_value(self.scroll[axis] / limits[axis] if limits[axis] else 0)
                thickness = min(self._scrollbar_thickness, base.size[1 - axis])
                rect = pygame.FRect(*base.topleft, 0, 0)
                if visible:
                    if axis == 0:
                        rect.update(base.left, base.bottom - thickness, viewport.width, thickness)
                    else:
                        rect.update(base.right - thickness, base.top, thickness, viewport.height)
                track.arrange(rect)
        finally:
            self._syncing_scrollbars = False

    def top_at(self, x, y):
        if not self.visible or not self.rect.collidepoint(x, y):
            return None
        for track in reversed(self._scrollbar_widgets):
            if track.visible and (hit := track.top_at(x, y)) is not None:
                return hit
        if not self.clip_children or self.get_inner_rect().collidepoint(x, y):
            for child in reversed(self.get_layout_children()):
                if child.visible and (hit := child.top_at(x, y)) is not None:
                    return hit
        return self

    def handle_event(self, event) -> None:
        if not self.visible or not self.is_enabled or getattr(event, "consumed", False):
            return
        if self.parent_scene and self.rect.collidepoint(*self.get_camera().get_mouse_pos()):
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP) and event.button in (4, 5):
                if any(self._bars):
                    event.consumed = True
                    return
            elif event.type == pygame.MOUSEWHEEL:
                self._handle_mouse_wheel(event)
        if not getattr(event, "consumed", False):
            super().handle_event(event)

    def _handle_mouse_wheel(self, event):
        keys = pygame.key.get_pressed()
        shift = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        horizontal, vertical = self._bars
        dx, dy = event.x, -event.y
        if horizontal and (shift or not vertical):
            dx += dy
            dy = 0
        before = self.scroll.copy()
        self.scroll_by((dx * self._scroll_speed, dy * self._scroll_speed))
        if self.scroll != before:
            event.consumed = True

    def draw(self, camera: bf.Camera) -> None:
        if not self.visible:
            return
        bf.Drawable.draw(self, camera)
        old_clip = camera.surface.get_clip()
        if self.clip_children:
            camera.surface.set_clip(camera.world_to_screen(self.get_inner_rect()).clip(old_clip))
        try:
            for child in self.get_layout_children():
                if child.visible:
                    child.draw(camera)
        finally:
            camera.surface.set_clip(old_clip)
        for track in self._scrollbar_widgets:
            if track.visible:
                track.draw(camera)

from typing import Self
import pygame
from .slider import Slider
import batFramework as bf
from .syncedVar import SyncedVar
from .container import Container
from .constraints.constraints import Fill,Center
from .widget import Widget
from .shape import Shape


class ScrollBar(Slider):
    def do_when_added(self):
        super().do_when_added()
        self.set_clip_children(False)
        self.set_pressed_relief(0).set_unpressed_relief(0)
        self.set_outline_width(0).set_border_radius(0)
        self.set_padding(0)
        self.meter.set_padding(2).set_outline_width(0)
        self.meter.content.set_padding(1).set_outline_width(0)
        self.meter.content.set_color(bf.color.TRANSPARENT)
        self.meter.handle.set_padding(0)

    def __str__(self):
        return "Scrollbar"

    def _on_synced_var_update(self, value):
        self.dirty_shape = True  # build uses synced var directly so we just trigger build via dirty shape
        if self.modify_callback:
            self.modify_callback(value)

    def on_get_focus(self, focus_area : pygame.Rect=None) -> None:
        self.is_focused = True
        self.do_on_get_focus()

    def draw_focused(self, camera):
        return

    def get_min_required_size(self):
        size = list(self.meter.get_min_required_size())
        return self.expand_rect_with_padding((0, 0, *size)).size

class ScrollingContainer(Container):
    def __init__(self, layout=None, *children):
        super().__init__(layout, *children)
        self.sync_scroll_x = SyncedVar(0)
        self.sync_scroll_y = SyncedVar(0)
        self.scrollbar_size = 10
        
        # Track whether scrollbars should be visible (computed, not affecting layout)
        self._show_x_scrollbar = False
        self._show_y_scrollbar = False

        # Create scrollbars
        self.y_scrollbar = (
            ScrollBar("", 0, synced_var=self.sync_scroll_y)
            .set_axis(bf.axis.VERTICAL)
            .set_autoresize(False)
            .set_direction(bf.direction.DOWN)
            .set_step(0.01)
            .set_padding(0)
        )
        self.y_scrollbar.meter.handle.set_autoresize_h(False)


        self.x_scrollbar = (
            ScrollBar("", 0, synced_var=self.sync_scroll_x)
            .set_autoresize(False)
            .set_step(0.01)
            .set_padding(0)
        )
        self.x_scrollbar.meter.handle.set_autoresize_w(False)


        # Bind scroll updates
        self.sync_scroll_x.bind(self, lambda v: self._on_scroll_sync())
        self.sync_scroll_y.bind(self, lambda v: self._on_scroll_sync())

        # Add scrollbars (they're children but not in layout)
        self.add(self.y_scrollbar, self.x_scrollbar)
        self.x_scrollbar.hide()
        self.y_scrollbar.hide()

    def __str__(self):
        return "Scrolling" + super().__str__()

    def set_scrollbar_size(self, size:int)->Self:
        self.scrollbar_size = size
        self.dirty_shape = True
        return self
    

    def get_inner_width(self):
        r = super().get_inner_width()
        if not  self._show_y_scrollbar:
            return r
        return r - self.scrollbar_size

    def get_inner_height(self):
        r = super().get_inner_height()
        if  not self._show_x_scrollbar:
            return r
        return r - self.scrollbar_size
    
    def get_inner_rect(self):
        r = super().get_inner_rect()
        if   self._show_y_scrollbar : 
            r.w -= self.scrollbar_size
        if   self._show_x_scrollbar :
            r.h -= self.scrollbar_size
        return r


    def expand_rect_with_padding(self, rect):
        r = super().expand_rect_with_padding(rect)

        if  self._show_y_scrollbar : 
            r.w += self.scrollbar_size
        if  self._show_x_scrollbar :
            r.h += self.scrollbar_size
        return r

    # ================================================================
    # Scroll conversion (normalized 0-1 ↔ pixel scroll)
    # ================================================================
    
    def _on_scroll_sync(self):
        """Convert normalized scroll to pixel scroll"""
        pixel_x = self._normalized_to_pixel_x(self.sync_scroll_x.value)
        pixel_y = self._normalized_to_pixel_y(self.sync_scroll_y.value)
        Container.set_scroll(self, (pixel_x, pixel_y))

    def set_scroll(self, value):
        """Override to update synced vars"""
        self.sync_scroll_x.value = self._pixel_to_normalized_x(value[0])
        self.sync_scroll_y.value = self._pixel_to_normalized_y(value[1])

    def _normalized_to_pixel_x(self, norm):
        content_w = self.layout.children_rect.w
        inner_w = self.get_inner_width()
        max_scroll = max(0, content_w - inner_w)
        return norm * max_scroll

    def _normalized_to_pixel_y(self, norm):
        content_h = self.layout.children_rect.h
        inner_h = self.get_inner_height()
        max_scroll = max(0, content_h - inner_h)
        return norm * max_scroll

    def _pixel_to_normalized_x(self, pixel):
        content_w = self.layout.children_rect.w
        inner_w = self.get_inner_width()
        max_scroll = max(0, content_w - inner_w)
        return pixel / max_scroll if max_scroll > 0 else 0

    def _pixel_to_normalized_y(self, pixel):
        content_h = self.layout.children_rect.h
        inner_h = self.get_inner_height()
        max_scroll = max(0, content_h - inner_h)
        return pixel / max_scroll if max_scroll > 0 else 0

    # ================================================================
    # Scrollbar management
    # ================================================================
        
    def _resolve_scrollbar_visibility(self):
        # Start assuming none visible
        show_x = False
        show_y = False

        while True:
            inner = super().get_inner_rect()

            if show_y:
                inner.w -= self.scrollbar_size
            if show_x:
                inner.h -= self.scrollbar_size

            content = self.layout.children_rect

            need_x = content.w > inner.w
            need_y = content.h > inner.h

            if need_x == show_x and need_y == show_y:
                break

            show_x = need_x
            show_y = need_y

        self._show_x_scrollbar = show_x
        self._show_y_scrollbar = show_y
        self.x_scrollbar.show() if self._show_x_scrollbar else self.x_scrollbar.hide()
        self.y_scrollbar.show() if self._show_y_scrollbar else self.y_scrollbar.hide()



    def _update_scrollbar_geometry(self):
        """Position and size scrollbars based on current state"""
        inner = self.get_inner_rect()
        outer = self.rect
        content = self.layout.children_rect

        # Compute ratios (how much of content is visible)
        x_ratio = min(1.0, inner.w / content.w if content.w > 0 else 1.0)
        y_ratio = min(1.0, inner.h / content.h if content.h > 0 else 1.0)

        # Update X scrollbar
        if self._show_x_scrollbar:
            bar_w = inner.w
            bar_h = self.scrollbar_size
            handle_w = max(20, bar_w * x_ratio)  # Min handle size
            
            self.x_scrollbar.set_size((bar_w, bar_h))
            self.x_scrollbar.set_position(inner.left, outer.bottom - bar_h - self.outline_width)
            self.x_scrollbar.meter.handle.set_size((handle_w, None))

        # Update Y scrollbar
        if self._show_y_scrollbar:
            bar_w = self.scrollbar_size
            bar_h = inner.h
            handle_h = max(20, bar_h * y_ratio)  # Min handle size
            
            self.y_scrollbar.set_size((bar_w, bar_h))
            self.y_scrollbar.set_position(outer.right - bar_w - self.outline_width, inner.top)
            self.y_scrollbar.meter.handle.set_size((None, handle_h))

    # ================================================================
    # Filter scrollbars from layout
    # ================================================================
    
    def get_layout_children(self):
        """Scrollbars are not part of layout"""
        return [
            c for c in self.children 
            if c not in [self.x_scrollbar, self.y_scrollbar]
        ]

    def get_interactive_children(self):
        """Scrollbars are not in tab order"""
        return [
            c for c in super().get_interactive_children()
            if c not in [self.x_scrollbar, self.y_scrollbar]
        ]

    def top_at(self, x, y):
        """Check scrollbars first (they're on top)"""
        if self.y_scrollbar.visible:
            res = self.y_scrollbar.top_at(x, y)
            if res:
                return res
        if self.x_scrollbar.visible:
            res = self.x_scrollbar.top_at(x, y)
            if res:
                return res
        return super().top_at(x, y)

    # ================================================================
    # Update cycle
    # ================================================================
    
    def apply_pre_updates(self):
        if self.dirty_size_constraints or self.dirty_shape:
            self.resolve_constraints(size_only=True)
            self.dirty_size_constraints = False
            self.dirty_position_constraints = True

        layout_changed = False

        if self.dirty_layout:
            self.layout.update_child_constraints()
            self.layout.arrange()
            self.dirty_layout = False
            layout_changed = True

        # Resolve visibility
        old_x = self._show_x_scrollbar
        old_y = self._show_y_scrollbar

        self._resolve_scrollbar_visibility()

        if old_x != self._show_x_scrollbar or old_y != self._show_y_scrollbar:
            # Show / hide actual widgets
            self.x_scrollbar.show() if self._show_x_scrollbar else self.x_scrollbar.hide()
            self.y_scrollbar.show() if self._show_y_scrollbar else self.y_scrollbar.hide()

            # Inner rect changed → relayout
            self.layout.update_child_constraints()
            self.layout.arrange()
            layout_changed = True

        old_scroll = self.scroll.xy
        self.clamp_scroll()

        if layout_changed or self.scroll.xy != old_scroll:
            self.layout.scroll_children()
            self.dirty_surface = True

        self._update_scrollbar_geometry()



    def handle_event(self, event):
        
        return super().handle_event(event)


    # ================================================================
    # Drawing with viewport clipping
    # ================================================================
    
    def draw(self, camera):
        """Draw container, then scrollbars on top"""
        # Draw background
        bf.Drawable.draw(self, camera)

        # Clip content area (accounting for scrollbars if visible)
        if self.clip_children:
            clip_rect = self.get_inner_rect()
            
            new_clip = camera.world_to_screen(clip_rect)
            old_clip = camera.surface.get_clip()
            new_clip = new_clip.clip(old_clip)
            camera.surface.set_clip(new_clip)

        # Draw content children
        for child in self.get_layout_children():
            if (not self.clip_children) or child.rect.colliderect(self.rect):
                child.draw(camera)
        
        if self.clip_children:
            camera.surface.set_clip(old_clip)

        # Draw scrollbars on top (unclipped)
        if self.x_scrollbar.visible:
            self.x_scrollbar.draw(camera)
        if self.y_scrollbar.visible:
            self.y_scrollbar.draw(camera)
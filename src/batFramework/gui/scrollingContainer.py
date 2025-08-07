from typing import Self

import pygame
from .slider import Slider
import batFramework as bf
from .syncedVar import SyncedVar
from .container import Container
from .constraints.constraints import FillX,FillY
from .widget import Widget



class ScrollBar(Slider):
    def do_when_added(self):
        super().do_when_added()
        self.meter.add_constraints(FillX(),FillY())
        self.set_clip_children(False)
        self.set_pressed_relief(0).set_unpressed_relief(0)
        self.meter.content.set_color(None)

    def _update_value(self,value):
        self.dirty_shape = True
        if self.modify_callback : 
            self.modify_callback(value)

    def on_get_focus(self) -> None:
        self.is_focused = True
        self.do_on_get_focus()
    def draw_focused(self, camera):
        return

class ScrollingContainer(Container):
    """
    Should work for single and double axis standard layouts 
    """
    def __init__(self, layout = None, *children):
        super().__init__(layout, *children)
        self.sync_scroll_x = SyncedVar(0)
        self.sync_scroll_y = SyncedVar(0)
        self.scrollbar_size = 8
        self.overflow = [False,False]

        self.v_scrollbar = (
            ScrollBar("",0,synced_var=self.sync_scroll_y).set_axis(bf.axis.VERTICAL)
            .set_autoresize(False)
            .set_padding(0)
            .set_direction(bf.direction.DOWN)
            .set_step(0.01)
        )
        self.v_scrollbar.handle.set_autoresize_h(False)


        self.h_scrollbar = (
            ScrollBar("",0,synced_var=self.sync_scroll_x)
            .set_autoresize(False)
            .set_padding(0)
            .set_step(0.01)
        )
        self.h_scrollbar.handle.set_autoresize_w(False)
        self.add(self.v_scrollbar)
        self.add(self.h_scrollbar)
        self.sync_scroll_x.bind_widget(self,self._update_scroll_x)
        self.sync_scroll_y.bind_widget(self,self._update_scroll_y)

    def top_at(self, x: float | int, y: float | int) -> "None|Widget":      

        if not self.rect.collidepoint(x,y):
            return None

        inner = self.get_inner_rect()
        res = None

        children = reversed(self.get_layout_children())
        if self.clip_children and inner.collidepoint(x, y):
            for c in children:
                res = c.top_at(x, y)
                if res:
                    return res
        elif not self.clip_children:
            for c in children:
                res = c.top_at(x, y)
                if res:
                    return res

        for sb in (self.v_scrollbar, self.h_scrollbar):
            res = sb.top_at(x, y)
            if res: return res
        
        return self

    def set_scrollbar_size(self,size:int)->Self:
        self.scrollbar_size= size
        self._update_scrollbars()
        return self

    def handle_event(self, event):
        super().handle_event(event)
        if event.consumed:return
        if event.type == pygame.MOUSEWHEEL and event.y != 0:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                self.sync_scroll_x.value += self.h_scrollbar.meter.step * (-1 if event.y > 0 else 1)
                self.clamp_scroll()
            else:    
                self.sync_scroll_y.value += self.h_scrollbar.meter.step * (-1 if event.y > 0 else 1)
                self.clamp_scroll()

    def set_scroll(self, value):
        super().set_scroll(value)
        if self.layout:
            content_width, content_height = self.layout.get_raw_size()
            visible_width, visible_height = self.get_inner_rect().size
            max_scroll_x = max(0, content_width - visible_width)
            max_scroll_y = max(0, content_height - visible_height)

            scroll_x_ratio = self.scroll.x / max_scroll_x if max_scroll_x > 0 else 0
            scroll_y_ratio = self.scroll.y / max_scroll_y if max_scroll_y > 0 else 0

            self.sync_scroll_x.value = scroll_x_ratio
            self.sync_scroll_y.value = scroll_y_ratio

    def _update_scroll_x(self, value):
        if self.layout:
            content_width = self.layout.get_raw_size()[0]
            visible_width = self.get_inner_width()
            max_scroll_x = max(0, content_width - visible_width)
            pixel_scroll_x = value * max_scroll_x
            self.set_scroll((pixel_scroll_x, self.scroll.y))

    def _update_scroll_y(self,value):
        if self.layout:
            content_height = self.layout.get_raw_size()[1]
            visible_height = self.get_inner_height()
            max_scroll_y = max(0, content_height - visible_height)
            pixel_scroll_y = value * max_scroll_y
            self.set_scroll((self.scroll.x, pixel_scroll_y))

    def get_layout_children(self):
        return [c for c in self.children if c not in [self.v_scrollbar,self.h_scrollbar]]

    def get_interactive_children(self):
        return [c for c in super().get_interactive_children() if c not in [self.v_scrollbar,self.h_scrollbar]]

    def _update_scrollbars(self):
        size = 8
        h_ratio = 0.5
        v_ratio = 0.5
        if self.layout:
            h_ratio = self.get_inner_width() / self.layout.get_raw_size()[0]
            v_ratio = self.get_inner_height() / self.layout.get_raw_size()[1]
        h_ratio = min(h_ratio, 1)
        v_ratio = min(v_ratio, 1)

        self.overflow = [h_ratio>=1,v_ratio>=1]
        self.h_scrollbar.set_visible(h_ratio<1)
        self.v_scrollbar.set_visible(v_ratio<1)

        self.v_scrollbar.set_size((size,self.rect.h))
        self.h_scrollbar.set_size((self.rect.width-self.v_scrollbar.rect.w ,size))
        self.v_scrollbar.set_position(self.rect.right-size,self.rect.y)
        self.h_scrollbar.set_position(self.rect.left,self.rect.bottom-size)

        h_handle_size = h_ratio * self.h_scrollbar.meter.get_inner_width()
        v_handle_size = v_ratio * self.v_scrollbar.meter.get_inner_height()

        h_handle_size = max(h_handle_size,8)
        v_handle_size= max(v_handle_size,8)


        self.h_scrollbar.handle.set_size((h_handle_size, None))
        self.v_scrollbar.handle.set_size((None, v_handle_size))


        self.h_scrollbar._align_composed()
        self.v_scrollbar._align_composed()

    def apply_pre_updates(self):
        if self.dirty_size_constraints or self.dirty_shape:
            self.resolve_constraints(size_only=True)
            self._update_scrollbars()

            self.dirty_size_constraints = False
            self.dirty_position_constraints = True

        if self.dirty_layout:
            self.layout.update_child_constraints()
            self.layout.arrange()
            self._update_scrollbars()
            self.dirty_layout = False

    def apply_post_updates(self, skip_draw = False):
        return super().apply_post_updates(skip_draw)

    def draw(self, camera):
        bf.Drawable.draw(self,camera)

        if self.clip_children:
            new_clip = camera.world_to_screen(self.get_inner_rect())
            old_clip = camera.surface.get_clip()
            new_clip = new_clip.clip(old_clip)
            camera.surface.set_clip(new_clip)

        # Draw each child widget, sorted by render order
        for child in sorted(self.get_layout_children(), key=lambda c: c.render_order):
            if (not self.clip_children) or (child.rect.colliderect(self.rect) or not child.rect):
                child.draw(camera)
                
        if self.clip_children:
            camera.surface.set_clip(old_clip)

        self.h_scrollbar.draw(camera)
        self.v_scrollbar.draw(camera)


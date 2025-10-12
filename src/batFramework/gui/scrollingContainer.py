from typing import Self
import pygame
from .slider import Slider
import batFramework as bf
from .syncedVar import SyncedVar
from .container import Container
from .constraints.constraints import FillX, FillY
from .widget import Widget
from .shape import Shape

class ScrollBar(Slider):
    def do_when_added(self):
        super().do_when_added()
        self.meter.add_constraints(FillX(), FillY())
        self.set_clip_children(False)
        self.set_pressed_relief(0).set_unpressed_relief(0)
        self.meter.content.set_color(None)

    def __str__(self):
        return "Scrollbar"

    def _on_synced_var_update(self, value):
        self.dirty_shape = True # build uses synced var directly so we just trigger build via dirty shape
        if self.modify_callback:
            self.modify_callback(value)

    def on_get_focus(self) -> None:
        self.is_focused = True
        self.do_on_get_focus()

    def draw_focused(self, camera):
        return
    
    def paint(self) -> None:
        Shape.paint(self)
 

class ScrollingContainer(Container):
    """
    Should work for single and double axis standard layouts 
    """
    def __init__(self, layout=None, *children):
        super().__init__(layout, *children)
        self.sync_scroll_x= SyncedVar(0) # 0 to 1
        self.sync_scroll_y= SyncedVar(0) # 0 to 1

        self.scrollbar_size = 8
        self.scrollbars_needed = [False, False]  # [horizontal, vertical]
        
        # Create scrollbars
        self.y_scrollbar = (
            ScrollBar("", 0, synced_var=self.sync_scroll_y)
            .set_axis(bf.axis.VERTICAL)
            .set_autoresize(False)
            .set_padding(0)
            .set_direction(bf.direction.DOWN)
            .set_step(0.01)
        )
        self.y_scrollbar.meter.handle.set_autoresize_h(False)

        self.x_scrollbar = (
            ScrollBar("", 0, synced_var=self.sync_scroll_x)
            .set_autoresize(False)
            .set_padding(0)
            .set_step(0.01)
        )

        self.x_scrollbar.meter.handle.set_autoresize_w(False)

        self.sync_scroll_x.bind(self,lambda v : self.on_sync_update((v,self.sync_scroll_y.value)))
        self.sync_scroll_y.bind(self,lambda v : self.on_sync_update((self.sync_scroll_x.value,v)))


        # Add scrollbars but initially hide them
        self.add(
            self.y_scrollbar,
            self.x_scrollbar
            )
        self.x_scrollbar.hide()
        self.y_scrollbar.hide()

    def __str__(self):
        return "Scrolling"+ super().__str__()

    def set_scroll(self,value):
        # print("Scrolling set scroll called", value)
        self.sync_scroll_x.value = self.x_scroll_scaled_to_normalized(value[0])
        self.sync_scroll_y.value = self.y_scroll_scaled_to_normalized(value[1])


    def on_sync_update(self,value):
        # print("Scrolling on sync update called", value)
        value = [self.x_scroll_normalized_to_scaled(value[0]),self.y_scroll_normalized_to_scaled(value[1])]
        super().set_scroll(value)


    def set_scrollbar_size(self, size:int)->Self:
        self.scrollbar_size = size
        self.dirty_layout= True
        self.dirty_shape = True
        return self

    def y_scroll_normalized_to_scaled(self, value):
        inner_height = self.get_inner_height()
        content_height = self.layout.children_rect.h  # total content height

        max_scroll = max(0, content_height - inner_height)
        converted_y = value * max_scroll

        return converted_y

    def x_scroll_normalized_to_scaled(self, value):
        inner_width = self.get_inner_width()
        content_width = self.layout.children_rect.w  # total content width

        max_scroll = max(0, content_width - inner_width)
        converted_x = value * max_scroll

        return converted_x

    def y_scroll_scaled_to_normalized(self, value):
        inner_height = self.get_inner_height()
        content_height = self.layout.children_rect.h

        max_scroll = max(0, content_height - inner_height)
        if max_scroll == 0:
            return 0
        return value / max_scroll

    def x_scroll_scaled_to_normalized(self, value):
        inner_width = self.get_inner_width()
        content_width = self.layout.children_rect.w

        max_scroll = max(0, content_width - inner_width)
        if max_scroll == 0:
            return 0
        return value / max_scroll



    def get_layout_children(self):
        return [c for c in super().get_layout_children() if c not in [self.y_scrollbar,self.x_scrollbar]]
    
    def get_interactive_children(self):
        return [c for c in super().get_interactive_children() if c not in [self.y_scrollbar,self.x_scrollbar]]

    def top_at(self, x, y):
        res = self.y_scrollbar.top_at(x,y)
        if res: return res
        res = self.x_scrollbar.top_at(x,y)
        if res: return res        
        return super().top_at(x, y)


    def get_inner_width(self):
        r = super().get_inner_width()
        if not  self.scrollbars_needed[1]:
            return r
        return r - self.scrollbar_size

    def get_inner_height(self):
        r = super().get_inner_height()
        if  not self.scrollbars_needed[0]:
            return r
        return r - self.scrollbar_size
    
    def get_inner_rect(self):
        r = super().get_inner_rect()
        if   self.scrollbars_needed[1] : 
            r.w -= self.scrollbar_size
        if   self.scrollbars_needed[0] :
            r.h -= self.scrollbar_size
        return r


    def expand_rect_with_padding(self, rect):
        r = super().expand_rect_with_padding(rect)

        if  self.scrollbars_needed[1] : 
            r.w += self.scrollbar_size
        if  self.scrollbars_needed[0] :
            r.h += self.scrollbar_size
        return r
    
    def _update_scrollbars(self):
        # print("Update scrollbar")
        if self.layout.children_rect.h == 0:
            y_ratio = 1 # set to 1 so no need to scroll
        else:
            y_ratio = self.get_inner_height() / self.layout.children_rect.h
        if self.layout.children_rect.w == 0:
            x_ratio = 1
        else:
            x_ratio = self.get_inner_width() / self.layout.children_rect.w


        tmp_scrollbars_needed = [
            x_ratio < 1,
            y_ratio < 1 
        ]
        visible_list = [self.x_scrollbar.visible,self.y_scrollbar.visible]
        # print(f"{tmp_scrollbars_needed=}")
        
        # print(f"{self.scrollbars_needed=}")

        # print(f"{x_ratio=}")
        # print(f"{y_ratio=}")


        # check if scrollbars changed (remove or add)
        if self.scrollbars_needed != tmp_scrollbars_needed :
            # self.dirty_shape = True # because scrollbars change self shape
            self.x_scrollbar.show() if tmp_scrollbars_needed[0] else self.x_scrollbar.hide()
            self.y_scrollbar.show() if tmp_scrollbars_needed[1] else self.y_scrollbar.hide()
        
            self.scrollbars_needed = tmp_scrollbars_needed
            



        if self.x_scrollbar.visible:
            self.x_scrollbar.set_size((self.rect.w-(self.scrollbar_size if tmp_scrollbars_needed[1] else 0),self.scrollbar_size))
            self.x_scrollbar.set_position(self.rect.left,self.rect.bottom - self.scrollbar_size)
            self.x_scrollbar.meter.handle.set_size((max(2,self.get_inner_width()*x_ratio),None))
        if self.y_scrollbar.visible:
            self.y_scrollbar.set_size((self.scrollbar_size,self.rect.h))
            self.y_scrollbar.set_position(self.rect.right - self.scrollbar_size,self.rect.top)
            self.y_scrollbar.meter.handle.set_size((None,max(self.get_inner_height()*y_ratio,2)))
        






    def build(self) -> None:
        if self.layout is not None:
            size = list(self.layout.get_auto_size())
            size[0]+=self.scrollbar_size
            size[1]+=self.scrollbar_size
            self.set_size(self.resolve_size(size))
        return super().build()

    def apply_pre_updates(self):
        if self.dirty_size_constraints or self.dirty_shape:
            self.resolve_constraints(size_only=True)
            self.dirty_size_constraints = False
            self.dirty_position_constraints = True

        if self.dirty_layout:
            self.layout.update_child_constraints()
            self.layout.arrange()
            self.dirty_layout = False
            self.dirty_scroll = True

        if self.dirty_scroll:
            self.layout.scroll_children()
            self._update_scrollbars()
            self.dirty_scroll = False


        


    def draw(self, camera):
        bf.Drawable.draw(self,camera)

        if self.clip_children:
            new_clip = camera.world_to_screen(self.get_inner_rect())
            old_clip = camera.surface.get_clip()
            new_clip = new_clip.clip(old_clip)
            camera.surface.set_clip(new_clip)

        # Draw each child widget, sorted by render order
        for child in self.children:
            if (not self.clip_children) or (child.rect.colliderect(self.rect) or not child.rect):
                child.draw(camera)
        if self.clip_children:
            camera.surface.set_clip(old_clip)

        self.y_scrollbar.draw(camera)
        self.x_scrollbar.draw(camera)

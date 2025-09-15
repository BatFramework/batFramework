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

    def _on_synced_var_update(self,value):
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
        super().__init__(layout,*children)
        self.sync_scroll_x = SyncedVar(0.0)
        self.sync_scroll_y = SyncedVar(0.0)
        self.scrollbar_size = 8
        self.overflow = [False,False]

        self.v_scrollbar = (
            ScrollBar("",0,synced_var=self.sync_scroll_y).set_axis(bf.axis.VERTICAL)
            .set_autoresize(False)
            .set_padding(0)
            .set_direction(bf.direction.DOWN)
            .set_step(0.01)
        )
        self.v_scrollbar.meter.handle.set_autoresize_h(False)

        self.h_scrollbar = (
            ScrollBar("",0,synced_var=self.sync_scroll_x)
            .set_autoresize(False)
            .set_padding(0)
            .set_step(0.01)
        )
        self.h_scrollbar.meter.handle.set_autoresize_w(False)

        

        self.add(
            self.v_scrollbar,
            self.h_scrollbar
        )


    def get_layout_children(self):
        return [c for c in self.children if c not in [self.v_scrollbar,self.h_scrollbar]]

    def get_interactive_children(self):
        return [c for c in super().get_interactive_children() if c not in [self.v_scrollbar,self.h_scrollbar]]



from typing import Literal

from .container import Container
from .scrollingContainer import ScrollingContainer
from .interactiveWidget import InteractiveWidget
from .toggle import Toggle
from .shape import Shape
from .indicator import ArrowIndicator
from .syncedVar import SyncedVar
from .layout import Column
import batFramework as bf
from .syncedVar import SyncedVar
from .widget import Widget
from .layout import Layout
from .constraints.constraints import AspectRatio


class CollapseIndicator(ArrowIndicator):
    def __init__(self, synced_var: SyncedVar[bool]):
        super().__init__(bf.direction.RIGHT)
        synced_var.bind(self, self.on_state_change)
        self.set_arrow_color(bf.color.BLACK)
        self.add_constraints(AspectRatio(1, reference_axis=bf.axis.VERTICAL))
        self.set_min_size((15,15))

    def on_state_change(self, state: bool):
        self.set_arrow_direction(bf.direction.DOWN if state else bf.direction.RIGHT)

    def top_at(self, x: float, y: float) -> "None|Widget":
        r = super().top_at(x, y)
        if r is self:
            return None
        return r


class CollapseContainer(Shape, InteractiveWidget):
    def __init__(self, text: str, layout: Layout = None, *children: Widget, **kwargs):
        super().__init__(**kwargs)
        self.state = SyncedVar[bool](True)
        self.state.bind(self, self._on_state_change)
        self.toggle = Toggle(text, synced_var=self.state)
        self.container = Container(layout, *children)
        self.add(self.toggle, self.container)
        self.state.value = False
        self.toggle.set_indicator(CollapseIndicator(self.state))
        self.toggle.indicator.add_constraints(
            bf.gui.AspectRatio(1, reference_axis=bf.axis.VERTICAL)
        )

    def __str__(self):
        return "CollapseContainer"

    def _on_state_change(self, value):
        if value:
            self.container.show() 
            self.container.dirty_surface = True

        else :
            self.container.hide()
        
        self.dirty_surface = True
        self.mark_shape_dirty()

    def allow_focus_to_self(self):
        return super().allow_focus_to_self() and self.toggle.allow_focus_to_self()

    def ask_focus(self):
        if self.allow_focus_to_self() and ((r := self.get_root()) is not None):
            r.focus_on(self.toggle)
            return True
        return False

    def measure_override(self, available_size):
        # These two children stretch across the control; their preferred width
        # is still intrinsic during measurement.
        toggle_size = self.toggle.measure(available_size)
        content_offer = (available_size[0], max(0, available_size[1] - toggle_size[1]))
        content_size = self.container.measure(content_offer)
        for child in self.children:
            if child not in (self.toggle, self.container):
                child.measure(available_size)
        height = toggle_size[1] + (content_size[1] if self.state.value else 0)
        return self.compute_min_size((max(toggle_size[0], content_size[0]) + self.padding[0] + self.padding[2],
                                      height + self.padding[1] + self.padding[3] + self.relief))

    def arrange_override(self):
        inner = self.get_inner_rect()
        toggle_height = min(inner.h, self.toggle.desired_size[1])
        self.toggle.arrange((inner.x, inner.y, inner.w, toggle_height))
        height = min(max(0, inner.h - toggle_height), self.container.desired_size[1]) if self.state.value else 0
        self.container.arrange((inner.x, inner.y + toggle_height, inner.w, height))
        self.arrange_children(exclude=(self.toggle, self.container))

    def get_min_required_size(self):
        return self.desired_size

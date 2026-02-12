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


class CollapseIndicator(ArrowIndicator):
    def __init__(self,synced_var:SyncedVar[bool]):
        super().__init__(bf.direction.RIGHT)
        synced_var.bind(self,self.on_state_change)

    def on_state_change(self,state:bool):
        self.set_arrow_direction(bf.direction.DOWN if state else bf.direction.RIGHT)

    def top_at(self, x: float, y: float) -> "None|Widget":
        r = super().top_at(x, y)
        if r is self:
            return None
        return r


class CollapseContainer(Shape,InteractiveWidget):
    def __init__(self, text:str, layout:Layout=None, *children:Widget, **kwargs):
        super().__init__(**kwargs)
        self.state = SyncedVar[bool](False)
        self.state.bind(self,self._on_state_change)
        self.toggle = Toggle(text,synced_var=self.state)
        self.toggle.set_autoresize_w(False)
        self.container = Container(layout,*children)
        self.container.set_autoresize_w(False)
        self.add(self.toggle,self.container)
        self.state.value = False
        self.toggle.set_indicator(CollapseIndicator(self.state))
        self.toggle.indicator.add_constraints(bf.gui.AspectRatio(1,reference_axis=bf.axis.VERTICAL))

    def __str__(self):
        return "CollapseContainer"

    def _on_state_change(self,value):
        print("state is ",value)
        self.container.show() if value else self.container.hide()
        self.dirty_shape = True

    def allow_focus_to_self(self):
        return super().allow_focus_to_self() and self.toggle.allow_focus_to_self()

    def get_focus(self):
        if self.allow_focus_to_self() and ((r := self.get_root()) is not None):
            r.focus_on(self.toggle)
            return True
        return False

    def build(self):
        res = False
        min_size = self.get_min_required_size()
        target_size = self.resolve_size(min_size)
        if self.rect.size != target_size :
            self.set_size(target_size)
            res = True

        inner = self.get_inner_rect()
        self.toggle.set_size((inner.w,None))
        self.toggle.set_position(*inner.topleft)
        if self.state.value:
            self.container.set_size((inner.w,None))
            self.container.set_position(*self.toggle.rect.bottomleft)
        return res

    def apply_updates(self, pass_type):

        if pass_type == "pre":
            self.apply_pre_updates()
            if self.state.value : self.container.apply_updates("pre")
            self.toggle.apply_updates("pre")
        elif pass_type == "post":
            if self.state.value : self.container.apply_updates("post")
            self.toggle.apply_updates("post")
            self.apply_post_updates(skip_draw=not self.visible)


    def get_min_required_size(self):
        t_min = self.toggle.get_min_required_size()
        if self.container.layout:
            c_min = self.container.expand_rect_with_padding((0,0,*self.container.layout.get_raw_size())).size
        else:
            c_min = self.container.get_min_required_size()
        if not self.state.value:
            c_min = (c_min[0],0)
        
        return self.expand_rect_with_padding((0,0,max(t_min[0],c_min[0]),t_min[1]+c_min[1])).size

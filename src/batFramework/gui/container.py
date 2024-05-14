import batFramework as bf
from .widget import Widget
from .shape import Shape
from .interactiveWidget import InteractiveWidget
from .layout import Layout,Column
from typing import Self
from pygame.math import Vector2



class Container(Shape,InteractiveWidget):
    def __init__(self, layout: Layout = Column(), *children: Widget)->None:
        super().__init__()
        self.set_debug_color("green")
        self.layout: Layout = layout
        self.scroll = Vector2(0,0)
        if self.layout:
            self.layout.set_parent(self)
        self.add_child(*children)

    def reset_scroll(self)->Self:
        self.scroll.update(0,0)
        return self
    
    def set_scroll(self,value:tuple)->Self:
        self.scroll.update(value)
        return self

    def scrollX_by(self,x:float|int)->Self:
        self.scroll.x += x 
        return self

    def scrollY_by(self,y: float|int)->Self:
        self.scroll.y += y 
        return self
    
    def scroll_by(self,value : tuple[float|int,float|int])->Self:
        self.scroll += value
        return self
    
    # def set_padding(self,value)->Self:
    #     return self

    def set_layout(self, layout: Layout) -> Self:
        self.layout = layout
        self.apply_constraints()
        return self

    def get_bounding_box(self):
        yield (self.rect, self.debug_color)        
        if self.children : yield (self.children[0].rect.unionall([c.rect for c in self.children[1:]]).move(-self.scroll),self.debug_color)
        for child in self.children:
            for data in child.get_bounding_box():
                yield (data[0].move(*-self.scroll),data[1])

    def get_interactive_children(self)->list[InteractiveWidget]:
        return [child for child in self.children if isinstance(child,InteractiveWidget)]

    def focus_next_child(self)->None:
        l = self.get_interactive_children()
        self.focused_index = min(self.focused_index + 1,len(l)-1)
        l[self.focused_index].get_focus()
        # moved = l[self.focused_index].rect.clamp(self.get_padded_rect())
        # self.set_scroll((moved.x - l[self.focused_index].rect.x,moved.y-l[self.focused_index].rect.y))


    def focus_prev_child(self)->None:
        l = self.get_interactive_children()
        self.focused_index = max(self.focused_index - 1,0)
        l[self.focused_index].get_focus()
        # moved = l[self.focused_index].rect.clamp(self.get_padded_rect())
        # self.set_scroll((moved.x - l[self.focused_index].rect.x,moved.y-l[self.focused_index].rect.y))

    def clear_children(self) -> None:
        self.children.clear()
        self.apply_constraints()

    def add_child(self, *child: Widget) -> Self:
        super().add_child(*child)
        if self.layout:
            self.layout.arrange()
        return self

    def remove_child(self, child: Widget) -> Self:
        super().remove_child(child)
        if self.layout:
            self.layout.arrange()
        return self

    def build(self) -> None:
        if self.layout:
            self.layout.arrange()
        super().build()

    def apply_constraints(self) -> None:
        super().apply_constraints()
        if self.layout:
            self.layout.arrange()

    def to_string_id(self) -> str:
        return f"Container({self.uid},{len(self.children)},{[c.to_string() for c in self.constraints]})"

    def notify(self)->None:
        self.apply_all_constraints()
        super().notify()

    

    def top_at(self, x: float|int, y: float|int) -> "None|Widget":
        if self.visible and self.rect.collidepoint(x, y):
            if self.children:
                for child in reversed(self.children):
                    r = child.top_at(x+self.scroll.x, y+self.scroll.y)
                    if r is not None:     
                        return r
            return self
        return None


    def get_focus(self) -> bool:
        res = super().get_focus()
        if not res : return False
        l = l = self.get_interactive_children()
        if not l : return True
        self.focused_index = min(self.focused_index,len(l))        
        return l[self.focused_index].get_focus()

    def set_focused_child(self,child:InteractiveWidget)->bool:
        l = self.get_interactive_children()
        i = l.index(child)
        if i >= 0 :
            self.focused_index = i
            return True
        return False

    def allow_focus_to_self(self) -> bool:
        return len(self.get_interactive_children())>0

    def draw(self, camera: bf.Camera) -> int:
        i = super().draw(camera)
        if i == 0 : return 0 
        camera.move_by(*self.scroll)
        j = sum((child.draw(camera) for child in self.children))
        camera.move_by(*(-self.scroll))
        return i + j
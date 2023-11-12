import batFramework as bf
from .widget import Widget
from .constraints import *
from typing import Self

class Layout:
    def __init__(self, parent: Widget=None):
        self.parent = parent
        self.child_constraints : list[Constraint] = []
        
    def set_child_constraints(self,*constraints)->Self:
        self.child_constraints = constraints
        self.arrange()
        return self
        
    def set_parent(self,parent:Widget):
        self.parent = parent
        self.arrange()

    def arrange(self)->None:
        raise NotImplementedError("Subclasses must implement arrange  method")

class Column(Layout):
    def __init__(self,gap:int=0,shrink:bool=False):
        super().__init__()
        self.gap = gap
        self.shrink :bool = shrink
        
    def arrange(self)->None:
        if not self.parent or not self.parent.children : return 
        if self.shrink:
            len_children = len(self.parent.children)
            parent_height = sum(c.rect.h for c in self.parent.children)
            parent_width = max(c.rect.w for c in self.parent.children)
            if self.gap  : parent_height += (len_children-1) * self.gap
            # print(self.parent.to_string(),len_children,parent_height)
            c = self.parent.get_constraint("height")
            if not c or c.height != parent_height : 
                self.parent.add_constraint(ConstraintHeight(parent_height))
            c = self.parent.get_constraint("width")
            if not c or c.width != parent_width : 
                self.parent.add_constraint(ConstraintWidth(parent_width))
        current_y = self.parent.rect.top

        for child in self.parent.children:
            child.set_position(self.parent.rect.x,current_y)
            current_y += child.rect.h + self.gap
            for c in self.child_constraints:
                if not child.has_constraint(c.name):
                    child.add_constraint(c)
            
class Row(Layout):
    def __init__(self, gap: int = 0, shrink: bool = False):
        super().__init__()
        self.gap = gap
        self.shrink = shrink

    def arrange(self) -> None:
        if not self.parent:
            return
        if self.shrink and self.parent.children:
            len_children = len(self.parent.children)
            parent_width = sum(c.rect.w for c in self.parent.children)
            parent_height = max(c.rect.h for c in self.parent.children)
            if self.gap:
                parent_width += (len_children - 1) * self.gap

            c = self.parent.get_constraint("width")
            if not c or c.width != parent_width:
                self.parent.add_constraint(ConstraintWidth(parent_width))
            c = self.parent.get_constraint("height")
            if not c or c.height != parent_height:
                self.parent.add_constraint(ConstraintHeight(parent_height))

        current_x = self.parent.rect.left
        for child in self.parent.children:
            child.set_position(current_x,self.parent.rect.y)
            current_x += child.rect.w + self.gap
            for c in self.child_constraints:
                if not child.has_constraint(c.name):
                    child.add_constraint(c)

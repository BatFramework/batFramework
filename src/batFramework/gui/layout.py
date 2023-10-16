import batFramework as bf
from .widget import Widget
from .constraints import *


class Layout:
    def __init__(self, parent: Widget=None):
        self.parent = parent

    def set_parent(self,parent:Widget):
        self.parent = parent
        self.arrange()

        
    def arrange(self)->None:
        raise NotImplementedError("Subclasses must implement arrange  method")

class ColumnLayout(Layout):
    def __init__(self,gap:int=0,*constraints:Constraint):
        super().__init__()
        self.gap = gap
        self.child_constraints : list[Constraint] = constraints 

    def arrange(self)->None:
        if not self.parent : return
        current_y = self.parent.rect.top
        
        for child in self.parent.children:
            for c in self.child_constraints:
                if not child.has_constraint(c.name):
                    child.add_constraint(c)
            child.set_y(current_y)
            current_y += child.rect.h + self.gap
            

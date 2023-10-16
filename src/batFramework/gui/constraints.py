from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .widget import Widget
import batFramework as bf

class Constraint:
    def __init__(self,name, priority=0):
        self.priority = priority
        self.name = name

    def set_priority(self, priority)->"Constraint":
        self.priority = priority
        return self

    def evaluate(self, parent_widget:Widget, child_widget:Widget) -> bool:
        raise NotImplementedError("Subclasses must implement evaluate method")

    def apply(self, parent_widget:Widget, child_widget:Widget=None) -> bool:
        if not self.evaluate(parent_widget, child_widget):
            self.apply_constraint(parent_widget, child_widget)
            return False
        return True
        
    def apply_constraint(self, parent_widget:Widget, child_widget:Widget):
        raise NotImplementedError("Subclasses must implement apply_constraint method")


class ConstraintMinWidth(Constraint):
    def __init__(self, width):
        super().__init__(name="min_width")
        self.min_width = width

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.width >= self.min_width

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_size(self.min_width,child_widget.rect.h)
    
class ConstraintCenterX(Constraint):
    def __init__(self):
        super().__init__(name="centerx")

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.centerx == parent_widget.rect.centerx

    def apply_constraint(self,parent_widget,child_widget):
        if not self.evaluate(parent_widget,child_widget):
            child_widget.set_center(parent_widget.rect.centerx,child_widget.rect.centery)

class ConstraintCenterY(Constraint):
    def __init__(self):
        super().__init__(name="centery")

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.centery == parent_widget.rect.centery

    def apply_constraint(self,parent_widget,child_widget):
        if not self.evaluate(parent_widget,child_widget):
            child_widget.set_center(child_widget.rect.centerx,parent_widget.rect.centery)

class ConstraintCenter(Constraint):
    def __init__(self):
        super().__init__(name="center")

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.center == parent_widget.rect.center

    def apply_constraint(self,parent_widget,child_widget):
        if not self.evaluate(parent_widget,child_widget):
            child_widget.set_center(*parent_widget.rect.center)

class ConstraintPercentageWidth(Constraint):
    def __init__(self,percentage:float,keep_autoresize:bool=True):
        super().__init__(name="percentage_width")
        self.percentage:float = percentage
        self.keep_autoresize: bool = keep_autoresize

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.width == round(parent_widget.rect.width * self.percentage)

    def apply_constraint(self,parent_widget,child_widget):
        if not self.evaluate(parent_widget,child_widget):
            if child_widget.autoresize:
                if self.keep_autoresize:
                    print(f"Warning: Constraint on {child_widget.to_string()} can't resize, autoresize set to True")
                    return 
                child_widget.set_autoresize(False)
            child_widget.set_size(round(parent_widget.rect.w * self.percentage) ,child_widget.rect.h)


class ConstraintPercentageHeight(Constraint):
    def __init__(self,percentage:float,keep_autoresize:bool=True):
        super().__init__(name="percentage_height")
        self.percentage:float = percentage
        self.keep_autoresize: bool = keep_autoresize

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.height == round(parent_widget.rect.height * self.percentage)

    def apply_constraint(self,parent_widget,child_widget):
        if not self.evaluate(parent_widget,child_widget):
            if child_widget.autoresize:
                if self.keep_autoresize:
                    print(f"Warning: Constraint on {child_widget.to_string()} can't resize, autoresize set to True")
                    return 
                child_widget.set_autoresize(False)
            child_widget.set_size(child_widget.rect.w,round(parent_widget.rect.h * self.percentage))


class ConstraintAspectRatio(Constraint):
    def __init__(self,ratio=1):
        super().__init__(name="aspect_ratio")
        if isinstance(ratio, float):
            self.ratio : float = ratio
        elif isinstance(ratio,Widget):
            self.ratio = ratio.rect.w / ratio.rect.h
        else:
            raise TypeError(f"Ratio must be float or Widget")
    def evaluate(self, parent_widget,child_widget):
        return  self.ratio  ==  child_widget.rect.w / child_widget.rect.h
        
    def apply_constraint(self,parent_widget,child_widget):
        if not self.evaluate(parent_widget,child_widget):
            return
from abc import ABC, abstractmethod
from ..widget import Widget
import batFramework as bf
import pygame


class Constraint:
    def __init__(self, name:str|None=None, priority=0):
        self.priority = priority
        self.name = name if name is not None else self.__class__.__name__
        self.old_autoresize_w = None
        self.old_autoresize_h = None
        self.affects_size : bool = False
        self.affects_position : bool = False


    def on_removal(self,child_widget: Widget)->None:
        child_widget.set_autoresize_h(self.old_autoresize_h)
        child_widget.set_autoresize_w(self.old_autoresize_w)


    def set_priority(self, priority) -> "Constraint":
        """
        Highest priority is used if 2 constraints are in conflict
        Default is 0
        """
        self.priority = priority
        return self

    def __str__(self) -> str:
        return f"{self.name.upper()}"

    def evaluate(self, parent_widget: Widget, child_widget: Widget) -> bool:
        raise NotImplementedError("Subclasses must implement evaluate method")

    def apply(self, parent_widget: Widget, child_widget: Widget = None) -> bool:
        if self.old_autoresize_h is None:
            self.old_autoresize_h = child_widget.autoresize_h
        if self.old_autoresize_w is None:
            self.old_autoresize_w = child_widget.autoresize_w

        if not self.evaluate(parent_widget, child_widget):
            self.apply_constraint(parent_widget, child_widget)
            return False
        return True

    def apply_constraint(self, parent_widget: Widget, child_widget: Widget):
        raise NotImplementedError("Subclasses must implement apply_constraint method")
    
    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return other.name == self.name

class MinWidth(Constraint):
    def __init__(self, width: float):
        super().__init__()
        self.min_width = width
        self.affects_size = True


    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.width >= self.min_width

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_autoresize_w(False)
        child_widget.set_size((self.min_width, None))

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.min_width == self.min_width
        )

class MinHeight(Constraint):
    def __init__(self, height: float):
        super().__init__()
        self.min_height = height
        self.affects_size = True


    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.h >= self.min_height
        

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_autoresize_h(False)
        child_widget.set_size((None, self.min_height))

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.min_height == self.min_height
        )

class MaxWidth(Constraint):
    def __init__(self, width: float):
        super().__init__()
        self.max_width = width
        self.affects_size = True

    def on_removal(self, child_widget: Widget) -> None:
        child_widget.set_autoresize_w(False)

    def evaluate(self, parent_widget, child_widget):
        res = child_widget.rect.width <= self.max_width
        if not res:
            child_widget.set_autoresize_w(False)
        return res

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_autoresize_w(True)
        current_height = child_widget.rect.height
        child_widget.set_size((self.max_width, current_height))

    def __eq__(self, other: "Constraint") -> bool:
        if not isinstance(other, self.__class__):
            return False
        return other.max_width == self.max_width


class MaxHeight(Constraint):
    def __init__(self, height: float):
        super().__init__()
        self.max_height = height
        self.affects_size = True

    def on_removal(self, child_widget: Widget) -> None:
        child_widget.set_autoresize_h(False)

    def evaluate(self, parent_widget, child_widget):
        res = child_widget.rect.height <= self.max_height
        if not res:
            child_widget.set_autoresize_h(False)
        return res

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_autoresize_h(True)
        current_width = child_widget.rect.width
        child_widget.set_size((current_width, self.max_height))

    def __eq__(self, other: "Constraint") -> bool:
        if not isinstance(other, self.__class__):
            return False
        return other.max_height == self.max_height



class CenterX(Constraint):
    def __init__(self):
        super().__init__()
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.centerx - parent_widget.get_inner_center()[0] == 0
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_center(
            parent_widget.get_inner_center()[0], child_widget.rect.centery
        )


class CenterY(Constraint):
    def __init__(self):
        super().__init__()
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.centery - parent_widget.get_inner_center()[1] == 0
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_center(
            child_widget.rect.centerx, parent_widget.get_inner_center()[1]
        )


class Center(Constraint):
    def __init__(self):
        super().__init__()
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.centerx - parent_widget.get_inner_center()[0] == 0
            and child_widget.rect.centery - parent_widget.get_inner_center()[1] == 0
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_center(*parent_widget.get_inner_center())


class PercentageWidth(Constraint):
    def __init__(self, percentage: float):
        super().__init__()
        self.percentage: float = percentage
        self.affects_size = True

    def on_removal(self, child_widget):
        child_widget.set_autoresize_w(True)

    def __str__(self) -> str:
        return f"{super().__str__()}.[{self.percentage*100}%]"

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.width == round(
            parent_widget.get_inner_width() * self.percentage
        )

    def apply_constraint(self, parent_widget, child_widget):
        if child_widget.autoresize_w:
            child_widget.set_autoresize_w(False)
        child_widget.set_size(
            (round(parent_widget.get_inner_width() * self.percentage), None)
        )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.percentage == self.percentage
        )


class PercentageHeight(Constraint):
    def __init__(self, percentage: float):
        super().__init__()
        self.percentage: float = percentage
        self.affects_size = True

    def on_removal(self, child_widget):
        child_widget.set_autoresize_h(True)


    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.height == round(
            parent_widget.get_inner_height() * self.percentage
        )

    def __str__(self) -> str:
        return f"{super().__str__()}.[{self.percentage*100}%]"

    def apply_constraint(self, parent_widget, child_widget):
        if child_widget.autoresize_h:
            child_widget.set_autoresize_h(False)
        child_widget.set_size(
            (None, round(parent_widget.get_inner_height() * self.percentage))
        )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.percentage == self.percentage
        )

class FillX(PercentageWidth):
    def __init__(self):
        super().__init__(1)
        self.name = "FillX"

    def __eq__(self, other: Constraint) -> bool:
        return Constraint.__eq__(self,other)

class FillY(PercentageHeight):
    def __init__(self):
        super().__init__(1)
        self.name = "FillY"

    def __eq__(self, other: Constraint) -> bool:
        return Constraint.__eq__(self,other)

class Fill(Constraint):
        def __init__(self):
            super().__init__()
            self.affects_size = True

        def on_removal(self, child_widget):
            child_widget.set_autoresize(True)

        def __str__(self) -> str:
            return f"{super().__str__()}"

        def evaluate(self, parent_widget, child_widget):
            return child_widget.rect.width == round(parent_widget.get_inner_width()) and \
                child_widget.rect.height == round(parent_widget.get_inner_height())
         
        def apply_constraint(self, parent_widget, child_widget):
            if child_widget.autoresize_w:
                child_widget.set_autoresize(False)
            child_widget.set_size(parent_widget.get_inner_rect().size)

        def __eq__(self,other:"Constraint")->bool:
            if not isinstance(other,self.__class__):
                return False
            return other.name == self.name 



class PercentageRectHeight(Constraint):
    def __init__(self, percentage: float):
        super().__init__()
        self.percentage: float = percentage
        self.affects_size = True

    def on_removal(self, child_widget):
        child_widget.set_autoresize_h(True)

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.height == round(
            parent_widget.rect.height * self.percentage
        )

    def __str__(self) -> str:
        return f"{super().__str__()}.[{self.percentage*100}%]"

    def apply_constraint(self, parent_widget, child_widget):
        if child_widget.autoresize_h:
            child_widget.set_autoresize_h(False)
        child_widget.set_size(
            (None, round(parent_widget.rect.height * self.percentage))
        )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.percentage == self.percentage
        )

class PercentageRectWidth(Constraint):
    def __init__(self, percentage: float):
        super().__init__()
        self.percentage: float = percentage
        self.affects_size = True

    def on_removal(self, child_widget: Widget) -> None:
        child_widget.set_autoresize_w(True)

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.width == round(
            parent_widget.rect.width * self.percentage
        )

    def __str__(self) -> str:
        return f"{super().__str__()}.[{self.percentage*100}%]"

    def apply_constraint(self, parent_widget, child_widget):
        if child_widget.autoresize_w:
            child_widget.set_autoresize_w(False)
        child_widget.set_size((round(parent_widget.rect.width * self.percentage), None))

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.percentage == self.percentage
        )

class FillRectX(PercentageRectWidth):
    def __init__(self):
        super().__init__(1)
        self.name = "fill_rect_x"
        self.affects_size = True


class FillRectY(PercentageRectHeight):
    def __init__(self):
        super().__init__(1)
        self.name = "fill_rect_y"
        self.affects_size = True


class AspectRatio(Constraint):
    def __init__(
        self,
        ratio: int | float | pygame.rect.FRectType = 1,
        reference_axis: bf.axis = bf.axis.HORIZONTAL,
    ):
        super().__init__()
        self.ref_axis: bf.axis = reference_axis
        self.affects_size = True

        if isinstance(ratio, float | int):
            self.ratio = ratio
        elif isinstance(ratio, pygame.rect.FRect):
            self.ratio = (
                round(ratio.w / ratio.h,2)
                if reference_axis == bf.axis.HORIZONTAL
                else round(ratio.h / ratio.w,2)
            )
        else:
            raise TypeError(f"Ratio must be float or FRect")

    def on_removal(self, child_widget):
        child_widget.set_autoresize(True)


    def evaluate(self, parent_widget, child_widget):
        if self.ref_axis == bf.axis.HORIZONTAL:
            return self.ratio == round(child_widget.rect.h / child_widget.rect.w,2)
        if self.ref_axis == bf.axis.VERTICAL:
            return self.ratio == round(child_widget.rect.w / child_widget.rect.h,2)


    def apply_constraint(self, parent_widget, child_widget):

        if self.ref_axis == bf.axis.VERTICAL:
            if child_widget.autoresize_w:
                child_widget.set_autoresize_w(False)
            child_widget.set_size((child_widget.rect.h * self.ratio, None))

        if self.ref_axis == bf.axis.HORIZONTAL:
            if child_widget.autoresize_h:
                child_widget.set_autoresize_h(False)

            child_widget.set_size((None, child_widget.rect.w * self.ratio))

    def __str__(self) -> str:
        return f"{self.name.upper()}[ratio = {self.ratio}, ref = {'Vertical' if self.ref_axis == bf.axis.VERTICAL else 'Horizontal'}]"


    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.ratio == self.ratio and
            other.ref_axis == self.ref_axis
        )

class AnchorBottom(Constraint):
    def __init__(self):
        super().__init__()
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.bottom
            == parent_widget.get_inner_bottom()
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            child_widget.rect.x, parent_widget.get_inner_bottom() - child_widget.rect.h
        )

class AnchorTop(Constraint):
    def __init__(self):
        super().__init__()
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return (child_widget.rect.top == parent_widget.get_inner_top())

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(child_widget.rect.x, parent_widget.get_inner_top())


class AnchorTopRight(Constraint):
    def __init__(self):
        super().__init__()
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.topright == parent_widget.get_inner_rect().topright

    def apply_constraint(self, parent_widget, child_widget):
        # print("before",child_widget.rect.topright, parent_widget.get_inner_rect().topright)
        topright = parent_widget.get_inner_rect().topright
        child_widget.set_position(topright[0] - child_widget.rect.w,topright[1])
        # print("after",child_widget.rect.topright, parent_widget.get_inner_rect().topright)

class AnchorTopLeft(Constraint):
    def __init__(self):
        super().__init__()
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.topleft == parent_widget.get_inner_rect().topleft

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(*parent_widget.get_inner_rect().topleft)


class AnchorBottomRight(Constraint):
    def __init__(self):
        super().__init__()
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.bottomright == parent_widget.get_inner_rect().bottomright
        )

    def apply_constraint(self, parent_widget, child_widget):
        bottomright =  parent_widget.get_inner_rect().bottomright

        child_widget.set_position(
            bottomright[0] - child_widget.rect.w,
            bottomright[1] - child_widget.rect.h,
        )


class AnchorRight(Constraint):
    def __init__(self):
        super().__init__()
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.right == parent_widget.get_inner_right()

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            parent_widget.get_inner_right() - child_widget.rect.w,
            None,
        )


class AnchorLeft(Constraint):
    def __init__(self):
        super().__init__()
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.left == parent_widget.get_inner_left()

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            parent_widget.get_inner_left(), None
        )


class Margin(Constraint):
    def __init__(self, margin_top: float = None, margin_right: float = None, margin_bottom: float = None, margin_left: float = None):
        """
        Applies margins in the order: top, right, bottom, left.
        Only non-None values are applied.
        """
        super().__init__()
        self.margins = (margin_top, margin_right, margin_bottom, margin_left)
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        # Check each margin if set, and compare the corresponding edge
        mt, mr, mb, ml = self.margins
        ok = True
        inner = parent_widget.get_inner_rect()
        if mt is not None:
            ok = ok and (child_widget.rect.top == inner.top + mt)
        if mr is not None:
            ok = ok and (child_widget.rect.right == inner.right - mr)
        if mb is not None:
            ok = ok and (child_widget.rect.bottom == inner.bottom - mb)
        if ml is not None:
            ok = ok and (child_widget.rect.left == inner.left + ml)
        return ok

    def apply_constraint(self, parent_widget, child_widget):
        # Get current position
        x, y = child_widget.rect.x, child_widget.rect.y
        w, h = child_widget.rect.w, child_widget.rect.h
        mt, mr, mb, ml = self.margins
        inner = parent_widget.get_inner_rect()
        # Calculate new x
        if ml is not None:
            x = inner.left + ml
        elif mr is not None:
            x = inner.right - w - mr

        # Calculate new y
        if mt is not None:
            y = inner.top + mt
        elif mb is not None:
            y = inner.bottom - h - mb

        child_widget.set_position(x, y)

    def __eq__(self, other: "Constraint") -> bool:
        if not isinstance(other, self.__class__):
            return False
        return other.margins == self.margins


class MarginBottom(Constraint):
    def __init__(self, margin: float):
        super().__init__()
        self.margin = margin
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.bottom == parent_widget.get_inner_bottom() - self.margin
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            child_widget.rect.x,
            parent_widget.get_inner_bottom() - child_widget.rect.h - self.margin,
        )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.margin == self.margin
        )

class MarginTop(Constraint):
    def __init__(self, margin: float):
        super().__init__()
        self.margin = margin
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.top == parent_widget.get_inner_top() + self.margin

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            child_widget.rect.x, parent_widget.get_inner_top() + self.margin
        )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.margin == self.margin
        )

class MarginLeft(Constraint):
    def __init__(self, margin: float):
        super().__init__()
        self.margin = margin
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.left == parent_widget.get_inner_left() + self.margin

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_position(
                parent_widget.get_inner_left() + self.margin, child_widget.rect.y
            )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.margin == self.margin
        )

class MarginRight(Constraint):
    def __init__(self, margin: float):
        super().__init__()
        self.margin = margin
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.right == parent_widget.get_inner_right() - self.margin

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            parent_widget.get_inner_right() - child_widget.rect.w - self.margin,
            child_widget.rect.y,
        )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.margin == self.margin
        )

class RectMarginBottom(Constraint):
    def __init__(self, margin: float):
        super().__init__()
        self.margin = margin
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.bottom == parent_widget.rect.bottom - self.margin
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            child_widget.rect.x,
            parent_widget.rect.bottom- child_widget.rect.h - self.margin,
        )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.margin == self.margin
        )

class RectMarginTop(Constraint):
    def __init__(self, margin: float):
        super().__init__()
        self.margin = margin
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.top == parent_widget.rect.top + self.margin

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            child_widget.rect.x, parent_widget.rect.top + self.margin
        )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.margin == self.margin
        )

class RectMarginLeft(Constraint):
    def __init__(self, margin: float):
        super().__init__()
        self.margin = margin
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.left == parent_widget.rect.left + self.margin

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_position(
                parent_widget.rect.left + self.margin, child_widget.rect.y
            )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.margin == self.margin
        )

class RectMarginRight(Constraint):
    def __init__(self, margin: float):
        super().__init__()
        self.margin = margin
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.right == parent_widget.rect.right - self.margin

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            parent_widget.rect.right - child_widget.rect.w - self.margin,
            child_widget.rect.y,
        )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.margin == self.margin
        )

class PercentageMarginBottom(Constraint):
    def __init__(self, margin: float):
        super().__init__()
        self.margin = margin
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return abs(
            child_widget.rect.bottom
            - (
                parent_widget.get_inner_bottom()- 
                parent_widget.get_inner_height() * self.margin)
        ) < 0.01

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            child_widget.rect.x,
            parent_widget.get_inner_bottom()
            - child_widget.rect.h
            - parent_widget.get_inner_height() * self.margin,
        )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.margin == self.margin
        )

class PercentageMarginTop(Constraint):
    def __init__(self, margin: float):
        super().__init__()
        self.margin = margin
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return abs(
            child_widget.rect.top
            - (
                parent_widget.get_inner_top()+ 
                parent_widget.get_inner_height() * self.margin)
        ) < 0.01

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            child_widget.rect.x,
            parent_widget.get_inner_top()
            + parent_widget.get_inner_height() * self.margin,
        )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.margin == self.margin
        )

class PercentageMarginLeft(Constraint):
    def __init__(self, margin: float):
        super().__init__()
        self.margin = margin
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.left
            == parent_widget.get_inner_left()
            + parent_widget.get_inner_width() * self.margin
        )

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_position(
                parent_widget.get_inner_left()
                + parent_widget.get_inner_width() * self.margin,
                child_widget.rect.y,
            )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.margin == self.margin
        )

class PercentageMarginRight(Constraint):
    def __init__(self, margin: float):
        super().__init__()
        self.margin = margin
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.right
            == parent_widget.get_inner_right()
            - parent_widget.get_inner_width() * self.margin
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            parent_widget.get_inner_right()
            - child_widget.rect.w
            - parent_widget.get_inner_width() * self.margin,
            child_widget.rect.y,
        )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.margin == self.margin
        )

class PercentageRectMarginBottom(Constraint):
    def __init__(self, margin: float):
        super().__init__()
        self.margin = margin
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.bottom
            == parent_widget.rect.top + parent_widget.rect.height * self.margin
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            child_widget.rect.x,
            parent_widget.rect.bottom
            - child_widget.rect.height
            - parent_widget.rect.height * self.margin,
        )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.margin == self.margin
        )

class PercentageRectMarginTop(Constraint):
    def __init__(self, margin: float):
        super().__init__()
        self.margin = margin
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.top
            == parent_widget.rect.top + parent_widget.rect.height * self.margin
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            child_widget.rect.x,
            parent_widget.rect.top + parent_widget.rect.height * self.margin,
        )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.margin == self.margin
        )

class PercentageRectMarginLeft(Constraint):
    def __init__(self, margin: float):
        super().__init__()
        self.margin = margin
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.left
            == parent_widget.rect.left + parent_widget.rect.width * self.margin
        )

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_position(
                parent_widget.rect.left + parent_widget.rect.width * self.margin,
                child_widget.rect.y,
            )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.margin == self.margin
        )

class PercentageRectMarginRight(Constraint):
    def __init__(self, margin: float):
        super().__init__()
        self.margin = margin
        self.affects_position = True

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.right
            == parent_widget.rect.right - parent_widget.rect.width * self.margin
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            parent_widget.rect.right
            - child_widget.rect.width
            - parent_widget.rect.width * self.margin,
            child_widget.rect.y,
        )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.margin == self.margin
        )




class Grow(Constraint, ABC):

    @abstractmethod
    def evaluate(self, parent_widget, child_widget):
        pass

    @abstractmethod
    def apply_constraint(self, parent_widget, child_widget):
        pass

    def __eq__(self, other: "Constraint") -> bool:
        return isinstance(other, self.__class__)


class GrowH(Grow):
    def __init__(self):
        super().__init__()
        self.affects_size = True

    def evaluate(self, parent_widget, child_widget):
        siblings = [s for s in parent_widget.children if s != child_widget]
        sibling_width = sum(s.rect.w for s in siblings)
        return abs(parent_widget.get_inner_width() - (child_widget.rect.w + sibling_width)) == 0

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_autoresize_w(False)
        siblings = [s for s in parent_widget.children if s != child_widget]
        sibling_width = sum(s.rect.w for s in siblings)
        # print(parent_widget.get_inner_width() - sibling_width," is new size")
        if hasattr(parent_widget,"layout"):
            w = parent_widget.layout.get_free_space()[0]
        else:
            w = parent_widget.get_inner_width()
        child_widget.set_size((w - sibling_width, None))


class GrowV(Grow):
    def __init__(self):
        super().__init__()
        self.affects_size = True

    def evaluate(self, parent_widget, child_widget):
        siblings = [s for s in parent_widget.children if s != child_widget]
        sibling_height = sum(s.rect.h for s in siblings)
        return abs(parent_widget.get_inner_height() - (child_widget.rect.h + sibling_height)) == 0

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_autoresize_h(False)
        siblings = [s for s in parent_widget.children if s != child_widget]
        sibling_height = sum(s.rect.h for s in siblings)
        if hasattr(parent_widget,"layou"):
            h = parent_widget.layout.get_free_space()[1]
        else:
            h = parent_widget.get_inner_height()
    
        child_widget.set_size((None, h- sibling_height))

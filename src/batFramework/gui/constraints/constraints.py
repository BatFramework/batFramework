from ..widget import Widget
import batFramework as bf
import pygame


class Constraint:
    def __init__(self, name:str|None=None, priority=0):
        self.priority = priority
        self.name = name if name is not None else self.__class__.__name__

    def on_removal(self,child_widget: Widget)->None:
        pass

    def set_priority(self, priority) -> "Constraint":
        self.priority = priority
        return self

    def __str__(self) -> str:
        return f"{self.name.upper()}"

    def evaluate(self, parent_widget: Widget, child_widget: Widget) -> bool:
        raise NotImplementedError("Subclasses must implement evaluate method")

    def apply(self, parent_widget: Widget, child_widget: Widget = None) -> bool:
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

    def on_removal(self, child_widget: Widget) -> None:
            return
            # child_widget.set_autoresize_w(False)

    def evaluate(self, parent_widget, child_widget):
        res =  child_widget.rect.width >= self.min_width
        # if not res:
            # child_widget.set_autoresize_w(False)
        return res

    def apply_constraint(self, parent_widget, child_widget):
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

    def on_removal(self, child_widget: Widget) -> None:
            child_widget.set_autoresize_h(False)

    def evaluate(self, parent_widget, child_widget):
        res = child_widget.rect.h >= self.min_height
        if not res:
            child_widget.set_autoresize_w(False)
        return res

    def apply_constraint(self, parent_widget, child_widget):
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

    def evaluate(self, parent_widget, child_widget):
        return (
            int(child_widget.rect.centerx - parent_widget.get_padded_center()[0]) == 0
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_center(
            parent_widget.get_padded_center()[0], child_widget.rect.centery
        )


class CenterY(Constraint):
    def __init__(self):
        super().__init__()

    def evaluate(self, parent_widget, child_widget):
        return (
            int(child_widget.rect.centery - parent_widget.get_padded_center()[1]) == 0
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_center(
            child_widget.rect.centerx, parent_widget.get_padded_center()[1]
        )


class Center(Constraint):
    def __init__(self):
        super().__init__()

    def evaluate(self, parent_widget, child_widget):
        return (
            int(child_widget.rect.centerx - parent_widget.get_padded_center()[0]) == 0
            and int(child_widget.rect.centery - parent_widget.get_padded_center()[1])
            == 0
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_center(*parent_widget.get_padded_center())


class PercentageWidth(Constraint):
    def __init__(self, percentage: float, keep_autoresize: bool = False):
        super().__init__()
        self.percentage: float = percentage
        self.keep_autoresize: bool = keep_autoresize

    def on_removal(self, child_widget: Widget) -> None:
        child_widget.set_autoresize_w(True)

    def __str__(self) -> str:
        return f"{super().__str__()}.[{self.percentage*100}%,keep_autoresize={self.keep_autoresize}]"

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.width == round(
            parent_widget.get_padded_width() * self.percentage
        )

    def apply_constraint(self, parent_widget, child_widget):
        if child_widget.autoresize_w:
            if self.keep_autoresize:
                print(
                    f"WARNING: Constraint on {child_widget.__str__()} can't resize, autoresize set to True"
                )
                return
            child_widget.set_autoresize_w(False)

        child_widget.set_size(
            (round(parent_widget.get_padded_width() * self.percentage), None)
        )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.percentage == self.percentage
        )


class PercentageHeight(Constraint):
    def __init__(self, percentage: float, keep_autoresize: bool = False):
        super().__init__()
        self.percentage: float = percentage
        self.keep_autoresize: bool = keep_autoresize

    def on_removal(self, child_widget: Widget) -> None:
        child_widget.set_autoresize_h(True)

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.height == round(
            parent_widget.get_padded_height() * self.percentage
        )

    def __str__(self) -> str:
        return f"{super().__str__()}.[{self.percentage*100}%,keep_autoresize={self.keep_autoresize}]"

    def apply_constraint(self, parent_widget, child_widget):
        if child_widget.autoresize_h:
            if self.keep_autoresize:
                print(
                    f"WARNING: Constraint on {child_widget} can't resize, autoresize set to True"
                )
                return
            child_widget.set_autoresize_h(False)
        child_widget.set_size(
            (None, round(parent_widget.get_padded_height() * self.percentage))
        )

    def __eq__(self,other:"Constraint")->bool:
        if not isinstance(other,self.__class__):
            return False
        return (
            other.name == self.name and
            other.percentage == self.percentage
        )

class FillX(PercentageWidth):
    def __init__(self, keep_autoresize: bool = False):
        super().__init__(1, keep_autoresize)
        self.name = "FillX"

    def __eq__(self, other: Constraint) -> bool:
        return Constraint.__eq__(self,other)

class FillY(PercentageHeight):
    def __init__(self, keep_autoresize: bool = False):
        super().__init__(1, keep_autoresize)
        self.name = "FillY"

    def __eq__(self, other: Constraint) -> bool:
        return Constraint.__eq__(self,other)


class PercentageRectHeight(Constraint):
    def __init__(self, percentage: float, keep_autoresize: bool = False):
        super().__init__()
        self.percentage: float = percentage
        self.keep_autoresize: bool = keep_autoresize

    def on_removal(self, child_widget: Widget) -> None:
        child_widget.set_autoresize_h(True)

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.height == round(
            parent_widget.rect.height * self.percentage
        )

    def __str__(self) -> str:
        return f"{super().__str__()}.[{self.percentage*100}%, keep_autoresize={self.keep_autoresize}]"

    def apply_constraint(self, parent_widget, child_widget):
        if child_widget.autoresize_h:
            if self.keep_autoresize:
                print(
                    f"WARNING: Constraint on {child_widget} can't resize, autoresize set to True"
                )
                return
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
    def __init__(self, percentage: float, keep_autoresize: bool = False):
        super().__init__()
        self.percentage: float = percentage
        self.keep_autoresize: bool = keep_autoresize

    def on_removal(self, child_widget: Widget) -> None:
        child_widget.set_autoresize_w(True)

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.width == round(
            parent_widget.rect.width * self.percentage
        )

    def __str__(self) -> str:
        return f"{super().__str__()}.[{self.percentage*100}%, keep_autoresize={self.keep_autoresize}]"

    def apply_constraint(self, parent_widget, child_widget):
        if child_widget.autoresize_w:
            if self.keep_autoresize:
                print(
                    f"WARNING: Constraint on {child_widget} can't resize, autoresize set to True"
                )
                return
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
    def __init__(self, keep_autoresize: bool = False):
        super().__init__(1, keep_autoresize)
        self.name = "fill_rect_x"


class FillRectY(PercentageRectHeight):
    def __init__(self, keep_autoresize: bool = False):
        super().__init__(1, keep_autoresize)
        self.name = "fill_rect_y"


class AspectRatio(Constraint):
    def __init__(
        self,
        ratio: int | float | pygame.rect.FRectType = 1,
        reference_axis: bf.axis = bf.axis.HORIZONTAL,
        keep_autoresize=False,
    ):
        super().__init__()
        self.ref_axis: bf.axis = reference_axis
        self.keep_autoresize: bool = keep_autoresize

        if isinstance(ratio, float | int):
            self.ratio = ratio
        elif isinstance(ratio, pygame.rect.FRect):
            self.ratio = (
                (ratio.w / ratio.h)
                if reference_axis == bf.axis.HORIZONTAL
                else (ratio.h / ratio.w)
            )
        else:
            raise TypeError(f"Ratio must be float or FRect")

    def on_removal(self, child_widget: Widget) -> None:
        child_widget.set_autoresize(True)


    def evaluate(self, parent_widget, child_widget):
        if self.ref_axis == bf.axis.HORIZONTAL:
            return self.ratio == child_widget.rect.h / child_widget.rect.w
        if self.ref_axis == bf.axis.VERTICAL:
            return self.ratio == child_widget.rect.w / child_widget.rect.h


    def apply_constraint(self, parent_widget, child_widget):

        if self.ref_axis == bf.axis.VERTICAL:
            if child_widget.autoresize_w:
                if self.keep_autoresize:
                    print(
                        f"WARNING: Constraint on {str(child_widget)} can't resize, autoresize set to True"
                    )
                    return
                child_widget.set_autoresize_w(False)
            child_widget.set_size((child_widget.rect.h * self.ratio, None))

        if self.ref_axis == bf.axis.HORIZONTAL:
            if child_widget.autoresize_h:
                if self.keep_autoresize:
                    print(
                        f"WARNING: Constraint on {str(child_widget)} can't resize, autoresize set to True"
                    )
                    return
                child_widget.set_autoresize_h(False)

            child_widget.set_size((None, child_widget.rect.w * self.ratio))

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

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.bottom
            == parent_widget.get_padded_bottom()
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            child_widget.rect.x, parent_widget.get_padded_bottom() - child_widget.rect.h
        )

class AnchorTop(Constraint):
    def __init__(self):
        super().__init__()

    def evaluate(self, parent_widget, child_widget):
        return (child_widget.rect.top == parent_widget.get_padded_top())

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(child_widget.rect.x, parent_widget.get_padded_top())


class AnchorTopRight(Constraint):
    def __init__(self):
        super().__init__()

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.topright == parent_widget.get_padded_rect().topright

    def apply_constraint(self, parent_widget, child_widget):
        # print("before",child_widget.rect.topright, parent_widget.get_padded_rect().topright)
        topright = parent_widget.get_padded_rect().topright
        child_widget.set_position(topright[0] - child_widget.rect.w,topright[1])
        # print("after",child_widget.rect.topright, parent_widget.get_padded_rect().topright)


class AnchorBottomRight(Constraint):
    def __init__(self):
        super().__init__()

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.bottomright == parent_widget.get_padded_rect().bottomright
        )

    def apply_constraint(self, parent_widget, child_widget):
        bottomright =  parent_widget.get_padded_rect().bottomright

        child_widget.set_position(
            bottomright[0] - child_widget.rect.w,
            bottomright[1] - child_widget.rect.h,
        )


class AnchorRight(Constraint):
    def __init__(self):
        super().__init__()

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.right == parent_widget.get_padded_right()

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            parent_widget.get_padded_right() - child_widget.rect.w,
            child_widget.rect.top,
        )


class AnchorLeft(Constraint):
    def __init__(self):
        super().__init__()

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.left == parent_widget.get_padded_left()

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            parent_widget.get_padded_left(), child_widget.rect.top
        )


class MarginBottom(Constraint):
    def __init__(self, margin: float):
        super().__init__()
        self.margin = margin

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.bottom == parent_widget.get_padded_bottom() - self.margin
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            child_widget.rect.x,
            parent_widget.get_padded_bottom() - child_widget.rect.h - self.margin,
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

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.top == parent_widget.get_padded_top() + self.margin

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            child_widget.rect.x, parent_widget.get_padded_top() + self.margin
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

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.left == parent_widget.get_padded_left() + self.margin

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_position(
                parent_widget.get_padded_left() + self.margin, child_widget.rect.y
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

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.right == parent_widget.get_padded_right() - self.margin

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            parent_widget.get_padded_right() - child_widget.rect.w - self.margin,
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

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.bottom
            == parent_widget.get_padded_top()
            + parent_widget.get_padded_height() * self.margin
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            child_widget.rect.x,
            parent_widget.get_padded_bottom()
            - child_widget.rect.h
            - parent_widget.get_padded_height() * self.margin,
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

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.top
            == parent_widget.get_padded_top()
            + parent_widget.get_padded_height() * self.margin
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            child_widget.rect.x,
            parent_widget.get_padded_top()
            + parent_widget.get_padded_height() * self.margin,
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

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.left
            == parent_widget.get_padded_left()
            + parent_widget.get_padded_width() * self.margin
        )

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_position(
                parent_widget.get_padded_left()
                + parent_widget.get_padded_width() * self.margin,
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

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.right
            == parent_widget.get_padded_right()
            - parent_widget.get_padded_width() * self.margin
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            parent_widget.get_padded_right()
            - child_widget.rect.w
            - parent_widget.get_padded_width() * self.margin,
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

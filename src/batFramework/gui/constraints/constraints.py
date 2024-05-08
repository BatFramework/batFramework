from ..widget import Widget
import batFramework as bf
import pygame
class Constraint:
    def __init__(self, name="Constraint", priority=0):
        self.priority = priority
        self.name = name

    def set_priority(self, priority) -> "Constraint":
        self.priority = priority
        return self

    def to_string(self) -> str:
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

class MinWidth(Constraint):
    def __init__(self, width:float):
        super().__init__(name="min_width")
        self.min_width = width

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.width >= self.min_width

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_size((self.min_width, child_widget.rect.h))

class MinHeight(Constraint):
    def __init__(self, height:float):
        super().__init__(name="min_height")
        self.min_height = height

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.h >= self.min_height

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_size((child_widget.rect.w,self.min_height))



class CenterX(Constraint):
    def __init__(self):
        super().__init__(name="centerx")

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.centerx == parent_widget.get_padded_center()[0]

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_center(
                parent_widget.get_padded_center()[0], child_widget.rect.centery
            )


class CenterY(Constraint):
    def __init__(self):
        super().__init__(name="centery")

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.centery == parent_widget.get_padded_center()[1]

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_center(
                child_widget.rect.centerx, parent_widget.get_padded_center()[1]
            )


class Center(Constraint):
    def __init__(self):
        super().__init__(name="center")

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.center == parent_widget.get_padded_center()

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_center(*parent_widget.get_padded_center())


class PercentageWidth(Constraint):
    def __init__(self, percentage: float, keep_autoresize: bool = False):
        super().__init__(name="percentage_width")
        self.percentage: float = percentage
        self.keep_autoresize: bool = keep_autoresize

    def to_string(self) -> str:
        return f"{super().to_string()}.[{self.percentage*100}%,keep_autoresize={self.keep_autoresize}]"

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.width == round(
            parent_widget.get_padded_width() * self.percentage
        )

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            if child_widget.autoresize:
                if self.keep_autoresize:
                    print(
                        f"WARNING: Constraint on {child_widget.to_string()} can't resize, autoresize set to True"
                    )
                    return
                child_widget.set_autoresize(False)
            child_widget.set_size((
                round(parent_widget.get_padded_width() * self.percentage),
                child_widget.rect.h,
            ))


class PercentageHeight(Constraint):
    def __init__(self, percentage: float, keep_autoresize: bool = False):
        super().__init__(name="percentage_height")
        self.percentage: float = percentage
        self.keep_autoresize: bool = keep_autoresize

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.height == round(
            parent_widget.get_padded_height() * self.percentage
        )
        
    def to_string(self) -> str:
        return f"{super().to_string()}.[{self.percentage*100}%,keep_autoresize={self.keep_autoresize}]"

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            if child_widget.autoresize:
                if self.keep_autoresize:
                    print(
                        f"WARNING: Constraint on {child_widget.to_string()} can't resize, autoresize set to True"
                    )
                    return
                child_widget.set_autoresize(False)
            child_widget.set_size((
                child_widget.rect.w,
                round(parent_widget.get_padded_height() * self.percentage),
            ))


class Height(Constraint):
    def __init__(self, height: float, keep_autoresize: bool = True):
        if height < 0:
            raise ValueError("height can't be negative")
        super().__init__(name="height")
        self.height = height
        self.keep_autoresize:bool = keep_autoresize

    def to_string(self) -> str:
        return f"{super().to_string()}.(height={self.height})"

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.height == self.height

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            if child_widget.autoresize:
                if self.keep_autoresize:
                    print(
                        f"WARNING: Constraint on {child_widget.to_string()} can't resize, autoresize set to True"
                    )
                    return
                child_widget.set_autoresize(False)
            child_widget.set_size((child_widget.rect.w, self.height))


class Width(Constraint):
    def __init__(self, width: float, keep_autoresize: bool = True):
        if width < 0:
            raise ValueError("width can't be negative")
        super().__init__(name="width")
        self.width = width
        self.keep_autoresize : bool = keep_autoresize

    def to_string(self) -> str:
        return f"{super().to_string()}.(width={self.width})"

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.width == self.width

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            if child_widget.autoresize:
                if self.keep_autoresize:
                    print(
                        f"WARNING: Constraint on {child_widget.to_string()} can't resize, autoresize set to True"
                    )
                    return
                child_widget.set_autoresize(False)
            child_widget.set_size((self.width, child_widget.rect.h))

#TODO 
class AspectRatio(Constraint):
    def __init__(self, ratio: int | float | pygame.rect.FRectType = 1, reference_axis:bf.axis = bf.axis.HORIZONTAL):
        super().__init__(name="aspect_ratio")
        if isinstance(ratio, float | int):
            self.ratio = ratio
        elif isinstance(ratio, pygame.rect.FRect):
            self.ratio = ratio.w / ratio.h
        else:
            raise TypeError(f"Ratio must be float or FRect")

    def evaluate(self, parent_widget, child_widget):
        return self.ratio == child_widget.rect.w / child_widget.rect.h

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            return  # TODO


class AnchorBottom(Constraint):
    def __init__(self):
        super().__init__(name="anchor_bottom")

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.top == parent_widget.get_padded_bottom() - child_widget.rect.h

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_y(parent_widget.get_padded_bottom() - child_widget.rect.h)


class AnchorTopRight(Constraint):
    def __init__(self):
        super().__init__(name="anchor_topright")

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.topright == parent_widget.get_padded_rect().topright

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_position(
                parent_widget.get_padded_right() - child_widget.rect.w,
                parent_widget.get_padded_top(),
            )

class AnchorBottomRight(Constraint):
    def __init__(self):
        super().__init__(name="anchor_bottomright")

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.bottomright == parent_widget.get_padded_rect().bottomright

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_position(
                parent_widget.get_padded_right() - child_widget.rect.w,
                parent_widget.get_padded_bottom() - child_widget.rect.h,
            )



class AnchorRight(Constraint):
    def __init__(self):
        super().__init__(name="anchor_right")

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.right == parent_widget.get_padded_right()

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_position(
                parent_widget.get_padded_right() - child_widget.rect.w,
                child_widget.rect.top,
            )


class AnchorLeft(Constraint):
    def __init__(self):
        super().__init__(name="anchor_left")

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.left == parent_widget.get_padded_left()

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_position(
                parent_widget.get_padded_left(), child_widget.rect.top
            )

class MarginBottom(Constraint):
    def __init__(self,margin:float):
        super().__init__(name="margin_bottom")
        self.margin = margin
    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.bottom == parent_widget.get_padded_bottom() - self.margin

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_y(parent_widget.get_padded_bottom() - child_widget.rect.h - self.margin)

class MarginTop(Constraint):
    def __init__(self,margin:float):
        super().__init__(name="margin_top")
        self.margin = margin
    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.top == parent_widget.get_padded_top() + self.margin

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_y(parent_widget.get_padded_top() + self.margin)

class MarginLeft(Constraint):
    def __init__(self,margin:float):
        super().__init__(name="margin_left")
        self.margin = margin
    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.left == parent_widget.get_padded_left() + self.margin

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_x(parent_widget.get_padded_left() + self.margin)

class MarginRight(Constraint):
    def __init__(self,margin:float):
        super().__init__(name="margin_right")
        self.margin = margin
    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.right == parent_widget.get_padded_right() + self.margin

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_x(parent_widget.get_padded_right()  -  child_widget.rect.w - self.margin)
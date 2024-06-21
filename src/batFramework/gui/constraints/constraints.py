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


class MinWidth(Constraint):
    def __init__(self, width: float):
        super().__init__(name="min_width")
        self.min_width = width

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.width >= self.min_width

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_size((self.min_width,None))


class MinHeight(Constraint):
    def __init__(self, height: float):
        super().__init__(name="min_height")
        self.min_height = height

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.h >= self.min_height

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_size((None, self.min_height))


class CenterX(Constraint):
    def __init__(self):
        super().__init__(name="centerx")

    def evaluate(self, parent_widget, child_widget):
        return int(child_widget.rect.centerx - parent_widget.get_padded_center()[0]) == 0 

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_center(
                parent_widget.get_padded_center()[0], child_widget.rect.centery
            )


class CenterY(Constraint):
    def __init__(self):
        super().__init__(name="centery")

    def evaluate(self, parent_widget, child_widget):
        return int(child_widget.rect.centery - parent_widget.get_padded_center()[1]) == 0 

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_center(
                child_widget.rect.centerx, parent_widget.get_padded_center()[1]
            )


class Center(Constraint):
    def __init__(self):
        super().__init__(name="center")

    def evaluate(self, parent_widget, child_widget):
        return int(child_widget.rect.centerx - parent_widget.get_padded_center()[0]) == 0 and \
        int(child_widget.rect.centery - parent_widget.get_padded_center()[1]) == 0

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_center(*parent_widget.get_padded_center())


class PercentageWidth(Constraint):
    def __init__(self, percentage: float, keep_autoresize: bool = False):
        super().__init__(name="percentage_width")
        self.percentage: float = percentage
        self.keep_autoresize: bool = keep_autoresize

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
            (
                round(parent_widget.get_padded_width() * self.percentage),None)
        )

class PercentageHeight(Constraint):
    def __init__(self, percentage: float, keep_autoresize: bool = False):
        super().__init__(name="percentage_height")
        self.percentage: float = percentage
        self.keep_autoresize: bool = keep_autoresize

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.height == round(parent_widget.get_padded_height() * self.percentage)

    def __str__(self) -> str:
        return f"{super().__str__()}.[{self.percentage*100}%,keep_autoresize={self.keep_autoresize}]"

    def apply_constraint(self, parent_widget, child_widget):
        if child_widget.autoresize_h:
            if self.keep_autoresize:
                print(f"WARNING: Constraint on {child_widget} can't resize, autoresize set to True")
                return
            child_widget.set_autoresize_h(False)
        child_widget.set_size((None,round(parent_widget.get_padded_height() * self.percentage)))

class FillX(PercentageWidth):
    def __init__(self, keep_autoresize: bool = False):
        super().__init__(1,keep_autoresize)
        self.name = "fill_x"

class FillY(PercentageHeight):
    def __init__(self, keep_autoresize: bool = False):
        super().__init__(1,keep_autoresize)
        self.name = "fill_y"


class Height(Constraint):
    def __init__(self, height: float, keep_autoresize: bool = False):
        if height < 0:
            raise ValueError("height can't be negative")
        super().__init__(name="height")
        self.height = height
        self.keep_autoresize: bool = keep_autoresize

    def __str__(self) -> str:
        return f"{super().__str__()}.(height={self.height})"

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.height == self.height

    def apply_constraint(self, parent_widget, child_widget):
        if child_widget.autoresize_h:
            if self.keep_autoresize:
                print(f"WARNING: Constraint on {child_widget.__str__()} can't resize, autoresize set to True")
                return
            child_widget.set_autoresize_h(False)
        child_widget.set_size((None, self.height))


class Width(Constraint):
    def __init__(self, width: float, keep_autoresize: bool = False):
        if width < 0:
            raise ValueError("width can't be negative")
        super().__init__(name="width")
        self.width = width
        self.keep_autoresize: bool = keep_autoresize

    def __str__(self) -> str:
        return f"{super().__str__()}.(width={self.width})"

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.width == self.width

    def apply_constraint(self, parent_widget, child_widget):
        if child_widget.autoresize_w:
            if self.keep_autoresize:
                print(
                    f"WARNING: Constraint on {child_widget.__str__()} can't resize, autoresize set to True"
                )
                return
            child_widget.set_autoresize_w(False)
        child_widget.set_size((self.width, None))


class AspectRatio(Constraint):
    def __init__(
        self,
        ratio: int | float | pygame.rect.FRectType = 1,
        reference_axis: bf.axis = bf.axis.HORIZONTAL,
        keep_autoresize=False,
    ):
        super().__init__(name="aspect_ratio")
        self.ref_axis : bf.axis = reference_axis
        self.keep_autoresize: bool = keep_autoresize

        if isinstance(ratio, float | int):
            self.ratio = ratio
        elif isinstance(ratio, pygame.rect.FRect):
            self.ratio = (ratio.w / ratio.h) if reference_axis == bf.axis.HORIZONTAL else (ratio.h / ratio.w)
        else:
            raise TypeError(f"Ratio must be float or FRect")

    def evaluate(self, parent_widget, child_widget):
        if self.ref_axis == bf.axis.HORIZONTAL:
            return self.ratio == child_widget.rect.w / child_widget.rect.h
        if self.ref_axis == bf.axis.VERTICAL:
            return self.ratio == child_widget.rect.h / child_widget.rect.w

    def apply_constraint(self, parent_widget, child_widget):

        if self.ref_axis == bf.axis.VERTICAL:
            if child_widget.autoresize_w :
                if self.keep_autoresize:
                    print(
                        f"WARNING: Constraint on {child_widget.__str__()} can't resize, autoresize set to True"
                    )
                    return
                child_widget.set_autoresize_w(False)
            child_widget.set_size((child_widget.rect.h * self.ratio,None))
        
        if self.ref_axis == bf.axis.HORIZONTAL:
            if child_widget.autoresize_h :
                if self.keep_autoresize:
                    print(
                        f"WARNING: Constraint on {child_widget.__str__()} can't resize, autoresize set to True"
                    )
                    return
                child_widget.set_autoresize_h(False)
            print("HERE")
            child_widget.set_size((None,child_widget.rect.w * self.ratio))

class AnchorBottom(Constraint):
    def __init__(self):
        super().__init__(name="anchor_bottom")

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.top == parent_widget.get_padded_bottom() - child_widget.rect.h

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(child_widget.rect.x,parent_widget.get_padded_bottom() - child_widget.rect.h)

class AnchorBottom(Constraint):
    def __init__(self):
        super().__init__(name="anchor_bottom")

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.top == parent_widget.get_padded_bottom() - child_widget.rect.h

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(child_widget.rect.x,parent_widget.get_padded_bottom() - child_widget.rect.h)



class AnchorTopRight(Constraint):
    def __init__(self):
        super().__init__(name="anchor_topright")

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.topright == parent_widget.get_padded_rect().topright

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            parent_widget.get_padded_right() - child_widget.rect.w,
            parent_widget.get_padded_top(),
        )


class AnchorBottomRight(Constraint):
    def __init__(self):
        super().__init__(name="anchor_bottomright")

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.bottomright == parent_widget.get_padded_rect().bottomright
        )

    def apply_constraint(self, parent_widget, child_widget):
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
        child_widget.set_position(
            parent_widget.get_padded_left(), child_widget.rect.top
        )


class MarginBottom(Constraint):
    def __init__(self, margin: float):
        super().__init__(name="margin_bottom")
        self.margin = margin

    def evaluate(self, parent_widget, child_widget):
        return (
            child_widget.rect.bottom == parent_widget.get_padded_bottom() - self.margin
        )

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(child_widget.rect.x,
            parent_widget.get_padded_bottom() - child_widget.rect.h - self.margin
        )

class MarginTop(Constraint):
    def __init__(self, margin: float):
        super().__init__(name="margin_top")
        self.margin = margin

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.top == parent_widget.get_padded_top() + self.margin

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(child_widget.rect.x,parent_widget.get_padded_top() + self.margin)


class MarginLeft(Constraint):
    def __init__(self, margin: float):
        super().__init__(name="margin_left")
        self.margin = margin

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.left == parent_widget.get_padded_left() + self.margin

    def apply_constraint(self, parent_widget, child_widget):
        if not self.evaluate(parent_widget, child_widget):
            child_widget.set_position(parent_widget.get_padded_left() + self.margin,child_widget.rect.y)


class MarginRight(Constraint):
    def __init__(self, margin: float):
        super().__init__(name="margin_right")
        self.margin = margin

    def evaluate(self, parent_widget, child_widget):
        return child_widget.rect.right == parent_widget.get_padded_right() - self.margin

    def apply_constraint(self, parent_widget, child_widget):
        child_widget.set_position(
            parent_widget.get_padded_right() - child_widget.rect.w - self.margin,
            child_widget.rect.y
        )

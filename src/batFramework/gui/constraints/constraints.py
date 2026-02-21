from abc import ABC, abstractmethod
from ..widget import Widget
import batFramework as bf
import pygame

class Constraint:
    def __init__(self, name: str | None = None, priority : int = 0):
        self.priority : int = priority
        self.name = name if name is not None else self.__class__.__name__
        self._saved_autoresize_w = None
        self._saved_autoresize_h = None
        self.affects_size: bool = False
        self.affects_position: bool = False

    def on_removal(self, child_widget: Widget) -> None:
        """Restore original autoresize state when constraint is removed"""
        if self._saved_autoresize_w is not None:
            child_widget.set_autoresize_w(self._saved_autoresize_w)
        if self._saved_autoresize_h is not None:
            child_widget.set_autoresize_h(self._saved_autoresize_h)

    def set_priority(self: int,  priority : int) -> "Constraint":
        self.priority = priority
        return self

    def __str__(self) -> str:
        return f"{self.name.upper()}"

    def evaluate(self, parent_widget: Widget, child_widget: Widget) -> bool:
        raise NotImplementedError("Subclasses must implement evaluate method")

    def apply(self, parent_widget: Widget, child_widget: Widget) -> bool:
        # Save original autoresize state on first application
        if self._saved_autoresize_w is None:
            self._saved_autoresize_w = child_widget.autoresize_w
        if self._saved_autoresize_h is None:
            self._saved_autoresize_h = child_widget.autoresize_h

        if not self.evaluate(parent_widget, child_widget):
            self.apply_constraint(parent_widget, child_widget)
            return False
        return True

    def apply_constraint(self, parent_widget: Widget, child_widget: Widget):
        raise NotImplementedError("Subclasses must implement apply_constraint method")

    def __eq__(self, other: "Constraint") -> bool:
        if not isinstance(other, self.__class__):
            return False
        return other.name == self.name


# ============================================================================
# Dimension Constraints (Width/Height)
# ============================================================================


class DimensionConstraint(Constraint):
    """Base class for width/height constraints with unit support"""

    def __init__(
        self,
        value: float,
        unit: bf.enums.unit = bf.enums.unit.PIXELS,
        axis: bf.axis = bf.axis.HORIZONTAL,
    ):
        super().__init__()
        self.value = value
        self.unit = unit
        self.axis = axis  # HORIZONTAL for width, VERTICAL for height
        self.affects_size = True

    def _get_parent_dimension(self, parent_widget: Widget) -> float:
        """Get the parent's dimension based on axis and unit"""
        if self.axis == bf.axis.HORIZONTAL:
            if self.unit == bf.enums.unit.PERCENTAGE_RECT:
                return parent_widget.rect.width
            else:
                return parent_widget.get_inner_width()
        else:  # VERTICAL
            if self.unit == bf.enums.unit.PERCENTAGE_RECT:
                return parent_widget.rect.height
            else:
                return parent_widget.get_inner_height()

    def _compute_size(self, parent_widget: Widget) -> float:
        """Compute the actual pixel size based on value and unit"""
        if self.unit == bf.enums.unit.PIXELS:
            return self.value
        else:  # PERCENTAGE or PERCENTAGE_RECT
            parent_dim = self._get_parent_dimension(parent_widget)
            return round(parent_dim * self.value)

    def _get_child_dimension(self, child_widget: Widget) -> float:
        """Get the child's current dimension"""
        return (
            child_widget.rect.width
            if self.axis == bf.axis.HORIZONTAL
            else child_widget.rect.height
        )

    def _set_child_dimension(self, child_widget: Widget, size: float):
        """Set the child's dimension"""
        if self.axis == bf.axis.HORIZONTAL:
            child_widget.set_size((size, None))
        else:
            child_widget.set_size((None, size))

    def __str__(self) -> str:
        axis_str = "W" if self.axis == bf.axis.HORIZONTAL else "H"
        if self.unit == bf.enums.unit.PIXELS:
            return f"{self.name.upper()}[{self.value}{self.unit.value}]"
        else:
            return f"{self.name.upper()}[{self.value * 100}{self.unit.value}]"


class Width(DimensionConstraint):
    """Set exact width"""

    def __init__(self, value: float, unit: bf.enums.unit = bf.enums.unit.PIXELS):
        super().__init__(value, unit, bf.axis.HORIZONTAL)
        self.name = f"Width"

    def on_removal(self, child_widget: Widget) -> None:
        child_widget.set_autoresize_w(self._saved_autoresize_w)

    def evaluate(self, parent_widget: Widget, child_widget: Widget) -> bool:
        target = self._compute_size(parent_widget)
        return child_widget.rect.width == target

    def apply_constraint(self, parent_widget: Widget, child_widget: Widget):
        child_widget.set_autoresize_w(False)
        self._set_child_dimension(child_widget, self._compute_size(parent_widget))


class Height(DimensionConstraint):
    """Set exact height"""

    def __init__(self, value: float, unit: bf.enums.unit = bf.enums.unit.PIXELS):
        super().__init__(value, unit, bf.axis.VERTICAL)
        self.name = f"Height"

    def on_removal(self, child_widget: Widget) -> None:
        child_widget.set_autoresize_h(self._saved_autoresize_h)

    def evaluate(self, parent_widget: Widget, child_widget: Widget) -> bool:
        target = self._compute_size(parent_widget)
        return child_widget.rect.height == target

    def apply_constraint(self, parent_widget: Widget, child_widget: Widget):
        child_widget.set_autoresize_h(False)
        self._set_child_dimension(child_widget, self._compute_size(parent_widget))


class MinWidth(DimensionConstraint):
    """Enforce minimum width"""

    def __init__(self, value: float, unit: bf.enums.unit = bf.enums.unit.PIXELS):
        super().__init__(value, unit, bf.axis.HORIZONTAL)

    def evaluate(self, parent_widget: Widget, child_widget: Widget) -> bool:
        return self._get_child_dimension(child_widget) >= self._compute_size(
            parent_widget
        )

    def apply_constraint(self, parent_widget: Widget, child_widget: Widget):
        child_widget.set_autoresize_w(False)
        self._set_child_dimension(child_widget, self._compute_size(parent_widget))


class MinHeight(DimensionConstraint):
    """Enforce minimum height"""

    def __init__(self, value: float, unit: bf.enums.unit = bf.enums.unit.PIXELS):
        super().__init__(value, unit, bf.axis.VERTICAL)

    def evaluate(self, parent_widget: Widget, child_widget: Widget) -> bool:
        return self._get_child_dimension(child_widget) >= self._compute_size(
            parent_widget
        )

    def apply_constraint(self, parent_widget: Widget, child_widget: Widget):
        child_widget.set_autoresize_h(False)
        self._set_child_dimension(child_widget, self._compute_size(parent_widget))


class MaxWidth(DimensionConstraint):
    """Enforce maximum width - allows autoresize up to the limit"""

    def __init__(self, value: float, unit: bf.enums.unit = bf.enums.unit.PIXELS):
        super().__init__(value, unit, bf.axis.HORIZONTAL)
        self._was_clamped = False

    def evaluate(self, parent_widget: Widget, child_widget: Widget) -> bool:
        max_size = self._compute_size(parent_widget)
        current_size = self._get_child_dimension(child_widget)

        if current_size > max_size:
            # Widget exceeded limit - clamp it
            self._was_clamped = True
            return False
        else:
            # Widget is within limit
            if self._was_clamped and current_size <= max_size:
                # Widget came back under limit - restore autoresize if it was originally enabled
                if self._saved_autoresize_w:
                    child_widget.set_autoresize_w(True)
                self._was_clamped = False
            return True

    def apply_constraint(self, parent_widget: Widget, child_widget: Widget):
        # Clamp to max size
        child_widget.set_autoresize_w(False)
        max_size = self._compute_size(parent_widget)
        self._set_child_dimension(child_widget, max_size)


class MaxHeight(DimensionConstraint):
    """Enforce maximum height - allows autoresize up to the limit"""

    def __init__(self, value: float, unit: bf.enums.unit = bf.enums.unit.PIXELS):
        super().__init__(value, unit, bf.axis.VERTICAL)
        self._was_clamped = False

    def evaluate(self, parent_widget: Widget, child_widget: Widget) -> bool:
        max_size = self._compute_size(parent_widget)
        current_size = self._get_child_dimension(child_widget)

        if current_size > max_size:
            # Widget exceeded limit - clamp it
            self._was_clamped = True
            return False
        else:
            # Widget is within limit
            if self._was_clamped and current_size <= max_size:
                # Widget came back under limit - restore autoresize if it was originally enabled
                if self._saved_autoresize_h:
                    child_widget.set_autoresize_h(True)
                self._was_clamped = False
            return True

    def apply_constraint(self, parent_widget: Widget, child_widget: Widget):
        # Clamp to max size
        child_widget.set_autoresize_h(False)
        max_size = self._compute_size(parent_widget)
        self._set_child_dimension(child_widget, max_size)


# ============================================================================
# Convenience Aliases (for backward compatibility)
# ============================================================================


class PercentageWidth(Width):
    def __init__(self, percentage: float):
        super().__init__(percentage, bf.enums.unit.PERCENTAGE)


class PercentageHeight(Height):
    def __init__(self, percentage: float):
        super().__init__(percentage, bf.enums.unit.PERCENTAGE)


class PercentageRectWidth(Width):
    def __init__(self, percentage: float):
        super().__init__(percentage, bf.enums.unit.PERCENTAGE_RECT)


class PercentageRectHeight(Height):
    def __init__(self, percentage: float):
        super().__init__(percentage, bf.enums.unit.PERCENTAGE_RECT)


class FillX(Width):
    def __init__(self):
        super().__init__(1.0, bf.enums.unit.PERCENTAGE)
        self.name = "FillX"


class FillY(Height):
    def __init__(self):
        super().__init__(1.0, bf.enums.unit.PERCENTAGE)
        self.name = "FillY"


class FillRectX(Width):
    def __init__(self):
        super().__init__(1.0, bf.enums.unit.PERCENTAGE_RECT)
        self.name = "FillRectX"


class FillRectY(Height):
    def __init__(self):
        super().__init__(1.0, bf.enums.unit.PERCENTAGE_RECT)
        self.name = "FillRectY"


class Fill(Constraint):
    """Fill both width and height of parent inner rect"""

    def __init__(self):
        super().__init__()
        self.affects_size = True

    def evaluate(self, parent_widget: Widget, child_widget: Widget) -> bool:
        return child_widget.rect.width == round(
            parent_widget.get_inner_width()
        ) and child_widget.rect.height == round(parent_widget.get_inner_height())

    def apply_constraint(self, parent_widget: Widget, child_widget: Widget):
        child_widget.set_autoresize(False)
        child_widget.set_size(parent_widget.get_inner_rect().size)


# ============================================================================
# Position Constraints (Anchoring)
# ============================================================================


class Anchor(Constraint):
    def __init__(self, edge: bf.bf.alignment):
        super().__init__()
        self.edge = edge.value  # e.g. "top", "center", "topleft"
        self.affects_position = True

    def _get_parent_inner_rect(self, parent_widget: Widget):
        return parent_widget.get_inner_rect()

    def evaluate(self, parent_widget: Widget, child_widget: Widget) -> bool:
        parent_rect = self._get_parent_inner_rect(parent_widget)
        return getattr(child_widget.rect, self.edge) == getattr(parent_rect, self.edge)

    def apply_constraint(self, parent_widget: Widget, child_widget: Widget):
        parent_rect = self._get_parent_inner_rect(parent_widget)
        value = getattr(parent_rect, self.edge)
        setattr(child_widget.rect, self.edge, value)


class AnchorTop(Anchor):
    def __init__(self):
        super().__init__(bf.alignment.TOP)


class AnchorBottom(Anchor):
    def __init__(self):
        super().__init__(bf.alignment.BOTTOM)


class AnchorLeft(Anchor):
    def __init__(self):
        super().__init__(bf.alignment.LEFT)


class AnchorRight(Anchor):
    def __init__(self):
        super().__init__(bf.alignment.RIGHT)


class AnchorTopLeft(Anchor):
    def __init__(self):
        super().__init__(bf.alignment.TOPLEFT)


class AnchorTopRight(Anchor):
    def __init__(self):
        super().__init__(bf.alignment.TOPRIGHT)


class AnchorBottomLeft(Anchor):
    def __init__(self):
        super().__init__(bf.alignment.BOTTOMLEFT)


class AnchorBottomRight(Anchor):
    def __init__(self):
        super().__init__(bf.alignment.BOTTOMRIGHT)


class CenterX(Anchor):
    def __init__(self):
        super().__init__(bf.alignment.CENTERX)


class CenterY(Anchor):
    def __init__(self):
        super().__init__(bf.alignment.CENTERY)


class Center(Anchor):
    def __init__(self):
        super().__init__(bf.alignment.CENTER)


# ============================================================================
# Margin Constraints
# ============================================================================
class Margin(Constraint):
    """Generic margin constraint with unit support
    
    Args:
        top: Top margin value (None to ignore)
        right: Right margin value (None to ignore)
        bottom: Bottom margin value (None to ignore)
        left: Left margin value (None to ignore)
        unit: Unit type for all margins (PIXELS, PERCENTAGE, or PERCENTAGE_RECT)
    
    Usage:
        Margin(10, 20, 30, 40)  # top, right, bottom, left in pixels
        Margin(10, None, 10, None)  # only top and bottom
        Margin(5, unit=bf.enums.unit.PERCENTAGE)  # only top, 5%
    """

    def __init__(
        self,
        left: float = None,
        top: float = None,
        right: float = None,
        bottom: float = None,
        *,
        unit: bf.enums.unit = bf.enums.unit.PIXELS
    ):
        super().__init__()
        self.top = top
        self.right = right
        self.bottom = bottom
        self.left = left
        self.unit = unit
        self.affects_position = True

    def _compute_margin(self, parent_widget: Widget, edge: str) -> float:
        """Compute the actual pixel margin based on value and unit for given edge"""
        value = getattr(self, edge)
        if value is None:
            return 0
            
        if self.unit == bf.enums.unit.PIXELS:
            return value

        # Get the dimension to calculate percentage from
        if edge in ("left", "right"):
            if self.unit == bf.enums.unit.PERCENTAGE_RECT:
                parent_dim = parent_widget.rect.width
            else:
                parent_dim = parent_widget.get_inner_width()
        else:  # top, bottom
            if self.unit == bf.enums.unit.PERCENTAGE_RECT:
                parent_dim = parent_widget.rect.height
            else:
                parent_dim = parent_widget.get_inner_height()

        return parent_dim * value

    def evaluate(self, parent_widget: Widget, child_widget: Widget) -> bool:
        results = []
        
        if self.top is not None:
            margin = self._compute_margin(parent_widget, "top")
            if self.unit == bf.enums.unit.PERCENTAGE_RECT:
                results.append(child_widget.rect.top == parent_widget.rect.top + margin)
            else:
                results.append(child_widget.rect.top == parent_widget.get_inner_top() + margin)
        
        if self.bottom is not None:
            margin = self._compute_margin(parent_widget, "bottom")
            if self.unit == bf.enums.unit.PERCENTAGE_RECT:
                results.append(child_widget.rect.bottom == parent_widget.rect.bottom - margin)
            else:
                results.append(child_widget.rect.bottom == parent_widget.get_inner_bottom() - margin)
        
        if self.left is not None:
            margin = self._compute_margin(parent_widget, "left")
            if self.unit == bf.enums.unit.PERCENTAGE_RECT:
                results.append(child_widget.rect.left == parent_widget.rect.left + margin)
            else:
                results.append(child_widget.rect.left == parent_widget.get_inner_left() + margin)
        
        if self.right is not None:
            margin = self._compute_margin(parent_widget, "right")
            if self.unit == bf.enums.unit.PERCENTAGE_RECT:
                results.append(child_widget.rect.right == parent_widget.rect.right - margin)
            else:
                results.append(child_widget.rect.right == parent_widget.get_inner_right() - margin)
        
        return all(results) if results else True

    def apply_constraint(self, parent_widget: Widget, child_widget: Widget):
        if self.top is not None:
            margin = self._compute_margin(parent_widget, "top")
            if self.unit == bf.enums.unit.PERCENTAGE_RECT:
                y = parent_widget.rect.top + margin
            else:
                y = parent_widget.get_inner_top() + margin
            child_widget.set_position(child_widget.rect.x, y)

        if self.bottom is not None:
            margin = self._compute_margin(parent_widget, "bottom")
            if self.unit == bf.enums.unit.PERCENTAGE_RECT:
                y = parent_widget.rect.bottom - margin - child_widget.rect.h
            else:
                y = parent_widget.get_inner_bottom() - margin - child_widget.rect.h
            child_widget.set_position(child_widget.rect.x, y)

        if self.left is not None:
            margin = self._compute_margin(parent_widget, "left")
            if self.unit == bf.enums.unit.PERCENTAGE_RECT:
                x = parent_widget.rect.left + margin
            else:
                x = parent_widget.get_inner_left() + margin
            child_widget.set_position(x, child_widget.rect.y)

        if self.right is not None:
            margin = self._compute_margin(parent_widget, "right")
            if self.unit == bf.enums.unit.PERCENTAGE_RECT:
                x = parent_widget.rect.right - margin - child_widget.rect.w
            else:
                x = parent_widget.get_inner_right() - margin - child_widget.rect.w
            child_widget.set_position(x, child_widget.rect.y)

    def __str__(self) -> str:
        parts = []
        for edge in ['top', 'right', 'bottom', 'left']:
            value = getattr(self, edge)
            if value is not None:
                if self.unit == bf.enums.unit.PIXELS:
                    parts.append(f"{edge}:{value}{self.unit.value}")
                else:
                    parts.append(f"{edge}:{value * 100}{self.unit.value}")
        return f"Margin[{', '.join(parts)}]" if parts else "Margin[]"


# Convenience aliases for margins
class MarginTop(Margin):
    def __init__(self, value: float, unit: bf.enums.unit = bf.enums.unit.PIXELS):
        super().__init__(top=value, unit=unit)


class MarginBottom(Margin):
    def __init__(self, value: float, unit: bf.enums.unit = bf.enums.unit.PIXELS):
        super().__init__(bottom=value, unit=unit)


class MarginLeft(Margin):
    def __init__(self, value: float, unit: bf.enums.unit = bf.enums.unit.PIXELS):
        super().__init__(left=value, unit=unit)


class MarginRight(Margin):
    def __init__(self, value: float, unit: bf.enums.unit = bf.enums.unit.PIXELS):
        super().__init__(right=value, unit=unit)


class PercentageMarginTop(Margin):
    def __init__(self, percentage: float):
        super().__init__(top=percentage, unit=bf.enums.unit.PERCENTAGE)


class PercentageMarginBottom(Margin):
    def __init__(self, percentage: float):
        super().__init__(bottom=percentage, unit=bf.enums.unit.PERCENTAGE)


class PercentageMarginLeft(Margin):
    def __init__(self, percentage: float):
        super().__init__(left=percentage, unit=bf.enums.unit.PERCENTAGE)


class PercentageMarginRight(Margin):
    def __init__(self, percentage: float):
        super().__init__(right=percentage, unit=bf.enums.unit.PERCENTAGE)


class PercentageRectMarginTop(Margin):
    def __init__(self, percentage: float):
        super().__init__(top=percentage, unit=bf.enums.unit.PERCENTAGE_RECT)


class PercentageRectMarginBottom(Margin):
    def __init__(self, percentage: float):
        super().__init__(bottom=percentage, unit=bf.enums.unit.PERCENTAGE_RECT)


class PercentageRectMarginLeft(Margin):
    def __init__(self, percentage: float):
        super().__init__(left=percentage, unit=bf.enums.unit.PERCENTAGE_RECT)


class PercentageRectMarginRight(Margin):
    def __init__(self, percentage: float):
        super().__init__(right=percentage, unit=bf.enums.unit.PERCENTAGE_RECT)
# ============================================================================
# Aspect Ratio Constraint
# ============================================================================


class AspectRatio(Constraint):
    def __init__(
        self,
        ratio: int | float | pygame.rect.FRect = 1,
        reference_axis: bf.axis = bf.axis.HORIZONTAL,
    ):
        super().__init__()
        self.ref_axis: bf.axis = reference_axis
        self.affects_size = True

        if isinstance(ratio, (float, int)):
            self.ratio = ratio
        elif isinstance(ratio, pygame.rect.FRect):
            self.ratio = (
                round(ratio.w / ratio.h, 2)
                if reference_axis == bf.axis.HORIZONTAL
                else round(ratio.h / ratio.w, 2)
            )
        else:
            raise TypeError(f"Ratio must be float or FRect")

    def evaluate(self, parent_widget: Widget, child_widget: Widget) -> bool:
        if self.ref_axis == bf.axis.HORIZONTAL:
            return self.ratio == round(child_widget.rect.h / child_widget.rect.w, 2)
        else:
            return self.ratio == round(child_widget.rect.w / child_widget.rect.h, 2)

    def apply_constraint(self, parent_widget: Widget, child_widget: Widget):
        if self.ref_axis == bf.axis.VERTICAL:
            child_widget.set_autoresize_w(False)
            child_widget.set_size((child_widget.rect.h * self.ratio, None))
        else:
            child_widget.set_autoresize_h(False)
            child_widget.set_size((None, child_widget.rect.w * self.ratio))

    def __str__(self) -> str:
        axis_name = "Vertical" if self.ref_axis == bf.axis.VERTICAL else "Horizontal"
        return f"{self.name.upper()}[ratio={self.ratio}, ref={axis_name}]"


# ============================================================================
# Grow Constraints (Fill remaining space)
# ============================================================================


class Grow(Constraint, ABC):
    @abstractmethod
    def evaluate(self, parent_widget: Widget, child_widget: Widget) -> bool:
        pass

    @abstractmethod
    def apply_constraint(self, parent_widget: Widget, child_widget: Widget):
        pass


class GrowH(Grow):
    def __init__(self):
        super().__init__()
        self.affects_size = True

    def evaluate(self, parent_widget: Widget, child_widget: Widget) -> bool:
        siblings = [s for s in parent_widget.children if s != child_widget]
        sibling_width = sum(s.rect.w for s in siblings)
        return (
            abs(parent_widget.get_inner_width() - (child_widget.rect.w + sibling_width))
            == 0
        )

    def apply_constraint(self, parent_widget: Widget, child_widget: Widget):
        child_widget.set_autoresize_w(False)
        siblings = [s for s in parent_widget.children if s != child_widget]
        sibling_width = sum(s.rect.w for s in siblings)

        if hasattr(parent_widget, "layout"):
            w = parent_widget.layout.get_free_space()[0]
        else:
            w = parent_widget.get_inner_width()

        child_widget.set_size((w - sibling_width, None))


class GrowV(Grow):
    def __init__(self):
        super().__init__()
        self.affects_size = True

    def evaluate(self, parent_widget: Widget, child_widget: Widget) -> bool:
        siblings = [s for s in parent_widget.children if s != child_widget]
        sibling_height = sum(s.rect.h for s in siblings)
        return (
            abs(
                parent_widget.get_inner_height()
                - (child_widget.rect.h + sibling_height)
            )
            == 0
        )

    def apply_constraint(self, parent_widget: Widget, child_widget: Widget):
        child_widget.set_autoresize_h(False)
        siblings = [s for s in parent_widget.children if s != child_widget]
        sibling_height = sum(s.rect.h for s in siblings)

        if hasattr(parent_widget, "layout"):
            h = parent_widget.layout.get_free_space()[1]
        else:
            h = parent_widget.get_inner_height()

        child_widget.set_size((None, h - sibling_height))

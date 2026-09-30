from abc import ABC, abstractmethod
import batFramework as bf
import pygame
from math import isfinite

class Constraint:
    def __init__(self, name: str | None = None, priority: int = 0):
        self.priority = priority
        self.name = name if name is not None else type(self).__name__
        self.affects_size = False
        self.affects_position = False

    def constrain_size(self, child_widget, preferred, available):
        """Return a preference without changing widgets or constraint state.

        Custom size constraints must implement this hook. `available` is the
        parent's offer, including infinity on unbounded scrolling axes.
        """
        if self.affects_size:
            raise NotImplementedError(f"{type(self).__name__} must implement constrain_size()")
        return preferred

    def constrain_position(
        self,
        proposed_rect: pygame.FRect,
        parent_rect: pygame.FRect,
        parent_inner_rect: pygame.FRect,
    ) -> pygame.FRect:
        """Return a positioned copy with the same size; never mutate inputs.

        All rectangles are in world coordinates. Bounds describe the parent's
        final outer box and content viewport, including padding and scrollbars.
        Custom position constraints implement this hook instead of moving widgets.
        """
        if self.affects_position:
            raise NotImplementedError(f"{type(self).__name__} must implement constrain_position()")
        return proposed_rect.copy()

    def set_priority(self, priority: int):
        self.priority = priority
        return self

    def __str__(self):
        return self.name.upper()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.name == self.name


class DimensionConstraint(Constraint):
    """A pure width/height policy. Parent maxima always take precedence."""

    def __init__(self, value, unit=bf.enums.unit.PIXELS, axis=bf.axis.HORIZONTAL):
        super().__init__()
        if not isfinite(value) or value < 0:
            raise ValueError("Dimension values must be finite and non-negative")
        self.value, self.unit, self.axis = value, unit, axis
        self.affects_size = True

    def constrain_size(self, child_widget, preferred, available):
        axis = 0 if self.axis == bf.axis.HORIZONTAL else 1
        reference = available[axis]
        if self.unit == bf.enums.unit.PERCENTAGE_RECT and child_widget.parent:
            parent = child_widget.parent
            reference = (parent._measure_size or parent.rect.size)[axis]
        value = self.value if self.unit == bf.enums.unit.PIXELS else reference * self.value
        if self.value == 0:
            value = 0
        if not isfinite(value):
            return preferred
        result = list(preferred)
        if isinstance(self, (MinWidth, MinHeight)):
            result[axis] = max(result[axis], value)
        elif isinstance(self, (MaxWidth, MaxHeight)):
            result[axis] = min(result[axis], value)
        else:
            result[axis] = value
        return tuple(result)

    def __str__(self):
        value = self.value if self.unit == bf.enums.unit.PIXELS else self.value * 100
        return f"{self.name.upper()}[{value}{self.unit.value}]"


class Width(DimensionConstraint):
    def __init__(self, value, unit=bf.enums.unit.PIXELS):
        super().__init__(value, unit, bf.axis.HORIZONTAL)
        self.name = "Width"


class Height(DimensionConstraint):
    def __init__(self, value, unit=bf.enums.unit.PIXELS):
        super().__init__(value, unit, bf.axis.VERTICAL)
        self.name = "Height"


class MinWidth(DimensionConstraint):
    def __init__(self, value, unit=bf.enums.unit.PIXELS):
        super().__init__(value, unit, bf.axis.HORIZONTAL)


class MinHeight(DimensionConstraint):
    def __init__(self, value, unit=bf.enums.unit.PIXELS):
        super().__init__(value, unit, bf.axis.VERTICAL)


class MaxWidth(DimensionConstraint):
    def __init__(self, value, unit=bf.enums.unit.PIXELS):
        super().__init__(value, unit, bf.axis.HORIZONTAL)


class MaxHeight(DimensionConstraint):
    def __init__(self, value, unit=bf.enums.unit.PIXELS):
        super().__init__(value, unit, bf.axis.VERTICAL)


# ============================================================================
# Convenience Aliases
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

    def constrain_size(self, child_widget, preferred, available):
        return tuple(limit if isfinite(limit) else value for value, limit in zip(preferred, available))

    def __init__(self):
        super().__init__()
        self.affects_size = True



# ============================================================================
# Position Constraints (Anchoring)
# ============================================================================


class Anchor(Constraint):
    def __init__(self, edge: bf.alignment):
        super().__init__()
        self.edge = edge.value  # e.g. "top", "center", "topleft"
        self.affects_position = True

    def constrain_position(self, proposed_rect, parent_rect, parent_inner_rect):
        rect = proposed_rect.copy()
        setattr(rect, self.edge, getattr(parent_inner_rect, self.edge))
        return rect


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
    """Position relative to parent edges without changing the assigned size.

    Arguments are left, top, right, bottom; None leaves that edge alone.
    Percentages use the content viewport, PERCENTAGE_RECT the outer rectangle.
    With opposing edges, right takes precedence over left and bottom over top.
    Negative margins are allowed to place a widget outside the reference box.
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

    def constrain_position(self, proposed_rect, parent_rect, parent_inner_rect):
        rect = proposed_rect.copy()
        bounds = parent_rect if self.unit == bf.enums.unit.PERCENTAGE_RECT else parent_inner_rect
        for edge in ("left", "top", "right", "bottom"):
            value = getattr(self, edge)
            if value is None:
                continue
            if self.unit != bf.enums.unit.PIXELS:
                value *= bounds.width if edge in ("left", "right") else bounds.height
            coordinate = getattr(bounds, edge)
            setattr(rect, edge, coordinate - value if edge in ("right", "bottom") else coordinate + value)
        return rect

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
    def constrain_size(self, child_widget, preferred, available):
        if self.ref_axis == bf.axis.HORIZONTAL:
            width = min(preferred[0], available[0], available[1] / self.ratio)
            return width, width * self.ratio
        height = min(preferred[1], available[1], available[0] / self.ratio)
        return height * self.ratio, height

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
        if not isfinite(self.ratio) or self.ratio <= 0:
            raise ValueError("Aspect ratio must be finite and positive")

    def __str__(self) -> str:
        axis_name = "Vertical" if self.ref_axis == bf.axis.VERTICAL else "Horizontal"
        return f"{self.name.upper()}[ratio={self.ratio}, ref={axis_name}]"


# ============================================================================
# Grow Constraints (Fill remaining space)
# ============================================================================

class Grow(Constraint, ABC):
    """Request a weighted share of remaining space from a Row or Column."""

    def __init__(self, weight=1.0):
        super().__init__()
        if not isfinite(weight):
            raise ValueError("Grow weights must be finite")
        self.weight = max(0.0, float(weight))
        self.affects_size = True

    @property
    @abstractmethod
    def axis(self):
        """0 for horizontal, 1 for vertical."""

    def constrain_size(self, child_widget, preferred, available):
        return preferred



class GrowH(Grow):
    axis = 0


class GrowV(Grow):
    axis = 1

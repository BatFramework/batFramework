import batFramework as bf
from .shape import Shape
from ..propertyEaser import PropertyEaser
from typing import Self
from .syncedVar import SyncedVar
from math import ceil


class Meter(Shape):
    """Base meter widget with value/range management."""

    def __init__(
        self,
        min_value: float = 0,
        max_value: float = None,
        step: float = 0.1,
        synced_var: SyncedVar = None,
    ):
        super().__init__()
        self.set_padding(0)
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.snap: bool = False
        self.synced_var = synced_var or SyncedVar(min_value)

        if self.max_value is None:
            self.max_value = self.synced_var.value

        # ----------------------------------------------------------
        # Animation
        # visual_ratio is what _build_content uses for drawing.
        # It trails the true ratio when animation is active,
        # and equals it instantly when animation_speed == 0.
        # ----------------------------------------------------------
        self.visual_ratio: float = self.get_ratio()
        self._animation_speed: float = 0.0   # 0 = instant
        self._easer: PropertyEaser | None = None

        self.synced_var.bind(self, self._on_synced_var_update)
        self.set_debug_color("pink")

    def __str__(self) -> str:
        return "Meter"

    # ==============================================================
    # Animation API
    # ==============================================================


    def set_animation_speed(self, speed: float) -> Self:
        """
        Set the easing duration in seconds for value changes.
        0 (default) = instant, no animation.
        """
        self._animation_speed = max(0.0, speed)
        if self._animation_speed == 0 and self._easer is not None:
            self._easer.stop()
        return self

    def _animate_to(self, target_ratio: float) -> None:
        """Start or restart the easer towards `target_ratio`."""
        if self._easer is None:
            self._easer = PropertyEaser(
                duration=self._animation_speed,
                easing=bf.easing.EASE_OUT,
            ).add_custom(
                getter=lambda: self.visual_ratio,
                setter=self._set_visual_ratio,
                end_value=target_ratio,
            )
        else:
            # Retarget: update end value and restart from current visual_ratio
            self._easer.stop()
            self._easer.properties[0].end_value = target_ratio

        self._easer.duration = self._animation_speed
        self._easer.start(force=True)

    def _set_visual_ratio(self, value: float) -> None:
        """Setter used by the easer — marks dirty so paint() is called."""
        self.visual_ratio = value
        self.dirty_shape = True

    # ==============================================================
    # Value management
    # ==============================================================

    def set_snap(self, snap: bool) -> Self:
        if self.snap != snap:
            self.snap = snap
            self.set_value(self.get_value())
        return self

    def set_step(self, step: float) -> Self:
        if self.step != step:
            self.step = step
            self.set_value(self.get_value())
        return self

    def set_range(self, range_min: float, range_max: float) -> Self:
        if range_min >= range_max:
            return self
        if self.min_value != range_min or self.max_value != range_max:
            self.min_value = range_min
            self.max_value = range_max
            self.visual_ratio = self.get_ratio()  # recompute with new range
            self.dirty_shape = True
        return self

    def set_value(self, value: float) -> Self:
        value = max(self.min_value, min(self.max_value, value))
        if self.snap:
            value = bf.utils.round_to_step_precision(value, self.step)
        self.synced_var.value = value
        return self

    def get_value(self) -> float:
        return self.synced_var.value

    def get_range(self) -> float:
        return self.max_value - self.min_value

    def get_ratio(self) -> float:
        """True ratio of the internal value — never used for drawing."""
        value_range = self.get_range()
        if value_range <= 0:
            return 0.0
        return (self.get_value() - self.min_value) / value_range

    def _on_synced_var_update(self, value: float) -> None:
        target = self.get_ratio()
        if self._animation_speed > 0:
            self._animate_to(target)
        else:
            self.visual_ratio = target
            self.dirty_shape = True

    def set_synced_var(self, synced_var: SyncedVar) -> Self:
        if self.synced_var:
            self.synced_var.unbind(self)
        self.synced_var = synced_var
        self.synced_var.bind(self, self._on_synced_var_update)
        self.dirty_shape = True
        return self


class BarMeter(Meter):
    """Meter with a visual fill bar showing the current value ratio."""

    def __init__(self, min_value=0, max_value=None, step=0.1, synced_var=None):
        super().__init__(min_value, max_value, step, synced_var)
        self.axis: bf.axis = bf.axis.HORIZONTAL
        self.direction: bf.direction = bf.direction.RIGHT

        self.content = Shape((4, 4)).set_color(bf.color.BLUE)
        self.content.set_debug_color("cyan")
        self.content.top_at = lambda x, y: self._content_top_at(x, y)
        self.add(self.content)
        self.content.set_outline_width(0)
        self.set_debug_color("pink")

    def __str__(self) -> str:
        return "BarMeter"

    def _content_top_at(self, x, y) -> Shape | None:
        if Shape.top_at(self.content, x, y) == self.content:
            return self
        return None

    def set_direction(self, direction: bf.direction) -> Self:
        if self.direction == direction:
            return self
        self.direction = direction
        if direction in [bf.direction.LEFT, bf.direction.RIGHT]:
            self.set_axis(bf.axis.HORIZONTAL)
        elif direction in [bf.direction.UP, bf.direction.DOWN]:
            self.set_axis(bf.axis.VERTICAL)
        self.dirty_shape = True
        return self

    def set_axis(self, axis: bf.axis) -> Self:
        if self.axis == axis:
            return self
        self.axis = axis
        if axis == bf.axis.HORIZONTAL:
            # self.content.set_autoresize_h(True).set_autoresize_w(False)
            if self.direction not in [bf.direction.LEFT, bf.direction.RIGHT]:
                self.set_direction(bf.direction.RIGHT)
        elif axis == bf.axis.VERTICAL:
            # self.content.set_autoresize_h(True).set_autoresize_w(False)
            if self.direction not in [bf.direction.UP, bf.direction.DOWN]:
                self.set_direction(bf.direction.UP)
        self.dirty_shape = True
        return self

    def build(self) -> bool:
        res = super().build()
        self._build_content()
        return res

    def _build_content(self) -> None:
        
        """Size and position the content bar using visual_ratio, not get_ratio()."""
        inner = self.get_inner_rect()
        ratio = self.visual_ratio          # ← animated display value

        self.content.set_border_radius(*[round(b / 2) for b in self.border_radius])

        outline = self.outline_width
        available_w = inner.width - outline * 2
        available_h = inner.height - outline * 2

        if self.axis == bf.axis.HORIZONTAL:
            content_w = max(0, ceil(available_w * ratio))
            content_h = available_h
            self.content.set_size((content_w, content_h))
            if self.direction == bf.direction.RIGHT:
                self.content.set_position(inner.left + outline, inner.top + outline)
            else:
                self.content.set_position(inner.right - outline - content_w, inner.top + outline)
        else:
            content_w = available_w
            content_h = max(0, ceil(available_h * ratio))
            self.content.set_size((content_w, content_h))
            if self.direction == bf.direction.UP:
                self.content.set_position(inner.left + outline, inner.bottom - outline - content_h)
            else:
                self.content.set_position(inner.left + outline, inner.top + outline)
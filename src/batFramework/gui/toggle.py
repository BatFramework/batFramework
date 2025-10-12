from .widget import Widget
from .button import Button
from .indicator import Indicator, ToggleIndicator
from .shape import Shape
import batFramework as bf
from typing import Self, Callable, Any
import pygame
from .syncedVar import SyncedVar  # Adjust import path

class Toggle(Button):
    def __init__(
        self,
        text: str = "",
        callback: Callable[[bool], Any] = None,
        default_value: bool = False,
        synced_var: SyncedVar[bool] = None,
    ) -> None:
        # Use passed SyncedVar or create a new one
        self.synced_var: SyncedVar[bool] = synced_var or SyncedVar(default_value)

        # Local value synced to SyncedVar.value
        self.value: bool = self.synced_var.value

        self.indicator: ToggleIndicator = ToggleIndicator(self.value)
        self.gap: float | int = 0
        self.spacing: bf.spacing = bf.spacing.MANUAL

        super().__init__(text, callback)

        # Add indicator to widget
        self.add(self.indicator)
        self.set_clip_children(False)

        # Bind this toggle’s _on_synced_var_update to synced_var updates
        self.synced_var.bind(self, self._on_synced_var_update)

    def _on_synced_var_update(self, new_value: bool) -> None:
        # Called when SyncedVar changes externally
        if self.value != new_value:
            self.set_value(new_value, do_callback=False)


    def set_indicator(self,indicator:Indicator):
        self.remove(self.indicator)
        self.synced_var.unbind(self.indicator)
        self.indicator = indicator
        self.add(self.indicator)
    def set_visible(self, value: bool) -> Self:
        self.indicator.set_visible(value)
        return super().set_visible(value)

    def set_value(self, value: bool, do_callback=False) -> Self:
        if self.value == value:
            return self  # No change

        self.value = value
        self.indicator.set_value(value)
        self.dirty_surface = True

        # Update SyncedVar only if different (avoid recursion)
        if self.synced_var.value != value:
            self.synced_var.value = value

        if do_callback and self.callback:
            self.callback(self.value)
        return self

    def set_spacing(self, spacing: bf.spacing) -> Self:
        if spacing == self.spacing:
            return self
        self.spacing = spacing
        self.dirty_shape = True
        return self

    def click(self) -> None:
        self.set_value(not self.value, do_callback=True)

    def set_gap(self, value: int | float) -> Self:
        value = max(0, value)
        if value == self.gap:
            return self
        self.gap = value
        self.dirty_shape = True
        return self

    def __str__(self) -> str:
        return f"Toggle({self.value})"

    def toggle(self) -> None:
        self.set_value(not self.value, do_callback=True)

    def get_min_required_size(self) -> tuple[float, float]:
        left = self.text_widget.get_min_required_size()
        gap = self.gap if self.text_widget.text else 0
        full_rect = pygame.FRect(0, 0, left[0] + left[1] + gap, left[1])
        full_rect.h += self.unpressed_relief
        return self.expand_rect_with_padding((0, 0, *full_rect.size)).size

    def _align_composed(self, left: Shape, right: Shape):
        full_rect = self.get_inner_rect()
        left_rect = left.rect
        right_rect = right.rect
        gap = {
            bf.spacing.MIN: 0,
            bf.spacing.HALF: (full_rect.width - left_rect.width - right_rect.width) // 2,
            bf.spacing.MAX: full_rect.width - left_rect.width - right_rect.width,
            bf.spacing.MANUAL: self.gap,
        }.get(self.spacing, 0)

        gap = max(0, gap)
        combined_width = left_rect.width + right_rect.width + gap

        group_x = {
            bf.alignment.LEFT: full_rect.left,
            bf.alignment.MIDLEFT: full_rect.left,
            bf.alignment.RIGHT: full_rect.right - combined_width,
            bf.alignment.MIDRIGHT: full_rect.right - combined_width,
            bf.alignment.CENTER: full_rect.centerx - combined_width // 2,
        }.get(self.alignment, full_rect.left)

        # Set horizontal positions
        left.set_position(x=group_x)
        right.set_position(x=group_x + left_rect.width + gap)

        # Set vertical positions
        if self.alignment in {bf.alignment.TOP, bf.alignment.TOPLEFT, bf.alignment.TOPRIGHT}:
            left.set_position(y=full_rect.top)
            right.set_position(y=full_rect.top)
        elif self.alignment in {bf.alignment.BOTTOM, bf.alignment.BOTTOMLEFT, bf.alignment.BOTTOMRIGHT}:
            left.set_position(y=full_rect.bottom - left_rect.height)
            right.set_position(y=full_rect.bottom - right_rect.height)
        else:
            left.set_center(y=full_rect.centery)
            right.set_center(y=full_rect.centery)

    def build(self) -> None:
        res = super().build()
        self.indicator.set_size(self.indicator.resolve_size((self.text_widget.rect.h, self.text_widget.rect.h)))
        self._align_composed(self.text_widget, self.indicator)
        return res

from .button import Button
from .indicator import Indicator, ToggleIndicator
import batFramework as bf
from typing import Self, Callable, Any
from .syncedVar import SyncedVar
from .widgetUtils import LayoutSlot, distribute_horizontal
from math import ceil


class Toggle(Button):
    def __init__(
        self,
        text: str = "",
        callback: Callable[[bool], Any] = None,
        default_value: bool = False,
        synced_var: SyncedVar[bool] | None = None,
    ) -> None:
        self.synced_var: SyncedVar[bool] = synced_var or SyncedVar(default_value)
        self.value: bool = self.synced_var.value

        self.indicator: ToggleIndicator = ToggleIndicator(self.value)
        self.gap: float | int = 0
        self.spacing: bf.spacing = bf.spacing.MANUAL

        super().__init__(text, callback)

        self.add(self.indicator)
        self.set_clip_children(False)

        self.synced_var.bind(self, self._update_state)

    def __str__(self) -> str:
        return f"Toggle({self.value})"

    # ------------------------------------------------------------
    # SyncedVar
    # ------------------------------------------------------------

    def _update_state(self, new_value: bool) -> None:
        if self.value != new_value:
            self.set_value(new_value, do_callback=False)

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------

    def set_indicator(self, indicator: Indicator) -> Self:
        self.remove(self.indicator)
        self.indicator = indicator
        self.add(indicator)
        self.dirty_shape = True
        return self

    def set_visible(self, value: bool) -> Self:
        self.indicator.set_visible(value)
        return super().set_visible(value)

    def set_value(self, value: bool, do_callback: bool = False) -> Self:
        if self.value == value:
            return self

        self.value = value
        self.indicator.set_value(value)
        self.dirty_surface = True

        if self.synced_var.value != value:
            self.synced_var.value = value

        if do_callback and self.callback:
            self.callback(value)

        return self

    def toggle(self) -> None:
        self.set_value(not self.value, do_callback=True)

    def click(self) -> None:
        self.toggle()

    def set_spacing(self, spacing: bf.spacing) -> Self:
        if spacing != self.spacing:
            self.spacing = spacing
            self.dirty_shape = True
        return self

    def set_gap(self, value: int | float) -> Self:
        value = max(0, value)
        if value != self.gap:
            self.gap = value
            self.dirty_shape = True
        return self

    # ------------------------------------------------------------
    # Sizing
    # ------------------------------------------------------------

    def get_min_required_size(self) -> tuple[float, float]:
        text_w, text_h = self.get_text_size()
        ind_size = max(self.font.get_height() // 2, 8)
        gap = self.gap if self.text else 0

        w = text_w + ind_size + gap
        h = max(text_h, ind_size) + self.unpressed_relief

        return self.expand_rect_with_padding((0, 0, w, h)).size

    # ------------------------------------------------------------
    # Layout (widgetUtils)
    # ------------------------------------------------------------

    def build(self) -> bool:
        res = super().build()

        local_inner = self.get_local_inner_rect()

        text_w, text_h = self.get_text_size()
        ind_size = max(self.font.get_height() // 2, 8)

        self.indicator.set_size(self.indicator.resolve_size((ind_size, ind_size)))

        has_text = bool(self.text)
        gap = (self.gap if self.text else 0) if self.spacing == bf.spacing.MANUAL else 0

        if self.spacing == bf.spacing.MAX and has_text:
            gap = max(0.0, local_inner.width - text_w - ind_size)

        ind_weight = 1 if self.spacing in (bf.spacing.MIN, bf.spacing.MANUAL) else 0

        if has_text:
            slots = [
                LayoutSlot((text_w, text_h), 0),
                LayoutSlot((ind_size, ind_size), ind_weight),
            ]
        else:
            slots = [LayoutSlot((ind_size, ind_size), ind_weight)]

        rects = distribute_horizontal(
            slots=slots,
            rect=local_inner,
            gap=gap,
            alignment=self.alignment,
        )

        # ---- Position text rect (LOCAL surface coords) ------------
        if has_text:
            text_rect = rects[0]
            ind_rect = rects[1]
            
            # Center text vertically in its slot
            tx = ceil(text_rect.left)
            ty = ceil(text_rect.centery - text_h / 2)
            self.text_rect.update(tx, ty, text_w, text_h)
        else:
            ind_rect = rects[0]

        # ---- Indicator position (WORLD coords) --------------------
        self.indicator.set_position(
            x=ind_rect.left + self.rect.x,
            y=ind_rect.top + self.rect.y,
        )

        return res
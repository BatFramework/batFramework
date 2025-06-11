from .button import Button
from .indicator import Indicator, ToggleIndicator
from .shape import Shape
import batFramework as bf
from typing import Self,Callable,Any

class Toggle(Button):
    def __init__(self, text: str = "", callback : Callable[[bool],Any]=None, default_value: bool = False) -> None:
        self.value: bool = default_value
        self.indicator: ToggleIndicator = ToggleIndicator(default_value)
        self.gap: float | int = 0
        self.spacing: bf.spacing = bf.spacing.MANUAL
        super().__init__(text, callback)
        self.add(self.indicator)
        self.set_clip_children(False)

    def set_visible(self, value: bool) -> Self:
        self.indicator.set_visible(value)
        return super().set_visible(value)

    def set_value(self, value: bool, do_callback=False) -> Self:
        self.value = value
        self.indicator.set_value(value)
        self.dirty_surface = True
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
        self.set_value(not self.value, True)

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
        if not self.text_rect:
            self.text_rect.size = self._get_text_rect_required_size()

        text_width, text_height = self.text_rect.size
        indicator_size = self.indicator.get_min_required_size()[1]
        gap = self.gap if self.text else 0

        total_width = text_width + gap + indicator_size
        total_height = text_height + self.unpressed_relief

        return self.expand_rect_with_padding((0, 0, total_width, total_height)).size

    def _build_composed_layout(self,other:Shape):
        size_changed = False
        self.text_rect.size = self._get_text_rect_required_size()

        gap = self.gap if self.text else 0
        full_rect = self.text_rect.copy()

        other_height = min(self.text_rect.h, self.font_object.get_height()+1)
        other.set_size(other.resolve_size((other_height,other_height)))
        
        full_rect.w += other.rect.w + gap
        full_rect.h += self.unpressed_relief
        

        # take into account the relief when calculating target size
        inflated = self.expand_rect_with_padding((0, 0, *full_rect.size)).size
        target_size = self.resolve_size(inflated)
        if self.rect.size != target_size:
            self.set_size(target_size)
            size_changed = True

        self._align_composed(other)
        return size_changed

    def _align_composed(self,other:Shape):
        
        full_rect = self.get_local_inner_rect()
        left_rect = self.text_rect
        right_rect = other.rect
        gap = {
            bf.spacing.MIN: 0,
            bf.spacing.HALF: (full_rect.width - left_rect.width - right_rect.width) // 2,
            bf.spacing.MAX: full_rect.width - left_rect.width - right_rect.width,
            bf.spacing.MANUAL: self.gap
        }.get(self.spacing, 0)

        gap = max(0, gap)
        combined_width = left_rect.width + right_rect.width + gap

        group_x = {
            bf.alignment.LEFT: full_rect.left,
            bf.alignment.MIDLEFT: full_rect.left,
            bf.alignment.RIGHT: full_rect.right - combined_width,
            bf.alignment.MIDRIGHT: full_rect.right - combined_width,
            bf.alignment.CENTER: full_rect.centerx - combined_width // 2
        }.get(self.alignment, full_rect.left)

        left_rect.x, right_rect.x = group_x, group_x + left_rect.width + gap

        if self.alignment in {bf.alignment.TOP, bf.alignment.TOPLEFT, bf.alignment.TOPRIGHT}:
            left_rect.top = right_rect.top = full_rect.top
        elif self.alignment in {bf.alignment.BOTTOM, bf.alignment.BOTTOMLEFT, bf.alignment.BOTTOMRIGHT}:
            left_rect.bottom = right_rect.bottom = full_rect.bottom
        else:
            left_rect.centery = right_rect.centery = full_rect.centery

        right_rect.move_ip(*self.rect.topleft)

    def _build_layout(self) -> None:
        return self._build_composed_layout(self.indicator)




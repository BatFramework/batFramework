import batFramework as bf
from .meter import Meter
from .button import Button
from .indicator import *
from .meter import Meter
from .shape import Shape
from .interactiveWidget import InteractiveWidget


class SliderHandle(Indicator, DraggableWidget):
    def __init__(self):
        super().__init__()
        self.set_color(bf.color.CLOUD_SHADE)
        self.old_key_repeat: tuple = (0, 0)
        self.parent : bf.ClickableWidget = self.parent
    def __str__(self) -> str:
        return "SliderHandle"

    def on_click_down(self, button: int) -> None:
        if not self.parent.is_enabled(): 
            return
        super().on_click_down(button)
        if button == 1:
            self.parent.get_focus()

    def on_exit(self) -> None:
        self.is_hovered = False
        self.do_on_exit()

    def do_on_drag(
        self, drag_start: tuple[float, float], drag_end: tuple[float, float]
    ) -> None:
        if not self.parent.is_enabled(): 
            return
        super().do_on_drag(drag_start, drag_end)
        m: Meter = self.parent.meter
        r = m.get_padded_rect()
        position = self.rect.centerx
        self.rect.clamp_ip(r)
        # Adjust handle position to value
        new_value = self.parent.position_to_value(position)
        self.parent.set_value(new_value)
        self.rect.centerx = self.parent.value_to_position(new_value)

    def top_at(self, x, y):
        return Widget.top_at(self, x, y)


class SliderMeter(Meter, InteractiveWidget):
    def __str__(self) -> str:
        return "SliderMeter"

    def on_click_down(self, button: int) -> None:
        if not self.parent.is_enabled(): 
            return
        if button == 1:
            self.parent.get_focus()
            r = self.get_root()
            if r:
                pos = r.drawing_camera.screen_to_world(pygame.mouse.get_pos())[0]
                self.parent.set_value(self.parent.position_to_value(pos))
        self.do_on_click_down(button)

class Slider(Button):
    def __init__(self, text: str, default_value: float = 1.0) -> None:
        super().__init__(text, None)
        self.gap: float | int = 0
        self.spacing: bf.spacing = bf.spacing.MANUAL
        self.modified_callback : Callable[[float],Any] = None
        self.meter: SliderMeter = SliderMeter()
        self.handle = SliderHandle()
        self.add(self.meter, self.handle)
        self.meter.set_debug_color(bf.color.RED)
        self.set_value(default_value, True)

    def set_visible(self, value: bool) -> Self:
        self.handle.set_visible(value)
        self.meter.set_visible(value)
        return super().set_visible(value)

    def __str__(self) -> str:
        return "Slider"

    def set_gap(self, value: int | float) -> Self:
        value = max(0, value)
        self.gap = value
        return self

    def do_on_get_focus(self) -> None:
        super().do_on_get_focus()
        self.old_key_repeat = pygame.key.get_repeat()
        pygame.key.set_repeat(200, 50)

    def do_on_lose_focus(self) -> None:
        super().do_on_lose_focus()
        pygame.key.set_repeat(*self.old_key_repeat)

    def set_spacing(self, spacing: bf.spacing) -> Self:
        if spacing == self.spacing:
            return self
        self.spacing = spacing
        self.dirty_shape = True
        return self

    def set_modify_callback(self, callback : Callable[[float],Any]) -> Self:
        self.modified_callback = callback
        return self

    def set_range(self, range_min: float, range_max: float) -> Self:
        self.meter.set_range(range_min, range_max)
        self.dirty_shape = True
        return self

    def set_step(self, step: float) -> Self:
        self.meter.set_step(step)
        self.dirty_shape = True
        return self

    def set_value(self, value, no_callback: bool = False) -> Self:
        if self.meter.value != value:
            self.meter.set_value(value)
            self.dirty_shape = True
        if self.modified_callback and (not no_callback):
            self.modified_callback(self.meter.value)
        return self

    def get_value(self) -> float:
        return self.meter.get_value()

    def do_on_key_down(self, key):
        if not self.is_enabled(): 
            return
        if key == pygame.K_RIGHT:
            self.set_value(self.meter.get_value() + self.meter.step)
        elif key == pygame.K_LEFT:
            self.set_value(self.meter.get_value() - self.meter.step)

    def do_on_click_down(self, button) -> None:
        if not self.is_enabled(): 
            return
        if button == 1:
            self.get_focus()

    def value_to_position(self, value: float) -> float:
        """
        Converts a value to a position on the meter, considering the step size.
        """
        rect = self.meter.get_padded_rect()
        value_range = self.meter.get_range()
        value = round(value / self.meter.step) * self.meter.step
        position_ratio = (value - self.meter.min_value) / value_range
        return (
            rect.left
            + (self.handle.rect.w / 2)
            + position_ratio * (rect.width - self.handle.rect.w)
        )

    def position_to_value(self, position: float) -> float:
        """
        Converts a position on the meter to a value, considering the step size.
        """
        handle_half = self.handle.rect.w / 2
        rect = self.meter.get_padded_rect()
        position = max(rect.left + handle_half, min(position, rect.right - handle_half))

        position_ratio = (position - rect.left - handle_half) / (
            rect.width - self.handle.rect.w
        )
        value_range = self.meter.get_range()
        value = self.meter.min_value + position_ratio * value_range
        return round(value / self.meter.step) * self.meter.step

    def get_min_required_size(self) -> tuple[float, float]:
        gap = self.gap if self.text else 0
        if not self.text_rect:
            self.text_rect.size = self._get_text_rect_required_size()
        w, h = self.text_rect.size
        h+=self.unpressed_relief
        return self.inflate_rect_by_padding((0, 0, w + gap + self.meter.get_min_required_size()[1], h)).size

    def _build_layout(self) -> None:

        gap = self.gap if self.text else 0
        self.text_rect.size = self._get_text_rect_required_size()

        #right part size
        meter_width = self.text_rect.h * 10
        if not self.autoresize_w:
            meter_width = self.get_padded_width() - self.text_rect.w - gap
        right_part_height = min(self.text_rect.h, self.font_object.point_size)
        self.meter.set_size_if_autoresize((meter_width,right_part_height))
        self.handle.set_size_if_autoresize((None,right_part_height))


        #join left and right
        joined_rect = pygame.FRect(
            0, 0, self.text_rect.w + gap + meter_width, self.text_rect.h
        )

        if self.autoresize_h or self.autoresize_w:
            target_rect = self.inflate_rect_by_padding(joined_rect)
            target_rect.h += self.unpressed_relief
            if not self.autoresize_w:
                target_rect.w = self.rect.w
            if not self.autoresize_h:
                target_rect.h = self.rect.h
            if self.rect.size != target_rect.size:
                self.set_size(target_rect.size)
                self.build()
                return

        # ------------------------------------ size is ok
        

        offset = self._get_outline_offset() if self.show_text_outline else (0,0)
        padded_rect = self.get_padded_rect()
        padded_relative = padded_rect.move(-self.rect.x, -self.rect.y)

        self.align_text(joined_rect, padded_relative.move( offset), self.alignment)
        self.text_rect.midleft = joined_rect.midleft

        if self.text:
            match self.spacing:
                case bf.spacing.MAX:
                    gap = padded_relative.right - self.text_rect.right - self.meter.rect.w
                case bf.spacing.MIN:
                    gap = 0

        # place meter

        pos = self.text_rect.move(
                self.rect.x + gap -offset[0],
                self.rect.y + (self.text_rect.h / 2) - (right_part_height / 2) -offset[1],
            ).topright
        self.meter.rect.topleft = pos
        # place handle

        x = self.value_to_position(self.meter.value)
        r = self.meter.get_padded_rect()
        self.handle.set_center(x, r.centery)

        # self.handle.set_center(x,self.rect.top)

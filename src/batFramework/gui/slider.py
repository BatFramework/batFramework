import batFramework as bf
from .meter import BarMeter
from .button import Button
from .indicator import *
from .meter import BarMeter
from .shape import Shape
from .interactiveWidget import InteractiveWidget

class SliderHandle(Indicator, DraggableWidget):
    def __init__(self):
        super().__init__()
        self.set_color(bf.color.CLOUD_SHADE)
        self.old_key_repeat: tuple = (0, 0)
        self.parent : bf.ClickableWidget = self.parent
        self.set_click_mask(1)
    def __str__(self) -> str:
        return "SliderHandle"

    def on_click_down(self, button: int) -> bool:
        if not self.parent.is_enabled: 
            return True
        res = super().on_click_down(button)
        if res : 
            self.parent.get_focus()
        return res
    
    def on_exit(self):
        before = self.is_clicked_down
        super().on_exit()
        self.is_clicked_down = before
    
    def do_on_drag(
        self, drag_start: tuple[float, float], drag_end: tuple[float, float]
    ) -> None:
        if not self.parent.is_enabled: 
            return
        super().do_on_drag(drag_start, drag_end)
        m: BarMeter = self.parent.meter
        r = m.get_inner_rect()

        position = self.rect.centerx if self.parent.axis == bf.axis.HORIZONTAL else self.rect.centery
        self.rect.clamp_ip(r)
        # Adjust handle position to value
        new_value = self.parent.position_to_value(position)
        self.parent.set_value(new_value)
        if self.parent.axis == bf.axis.HORIZONTAL:
            self.rect.centerx = self.parent.value_to_position(new_value)
        else:
            self.rect.centery = self.parent.value_to_position(new_value)

    def top_at(self, x, y):
        return Widget.top_at(self, x, y)

class SliderMeter(BarMeter, InteractiveWidget):
    def __str__(self) -> str:
        return "SliderMeter"

    def __init__(self, min_value = 0, max_value = 1, step = 0.1):
        super().__init__(min_value, max_value, step)
        self.set_padding(0)

    def get_min_required_size(self):
        size = list(super().get_min_required_size())
        if self.parent.axis == bf.axis.HORIZONTAL:
            size[0] = size[1]*3
        else:
            size[1] = size[0]*3
        return self.resolve_size(size)

    def on_click_down(self, button: int) -> bool:
        if not self.parent.is_enabled: 
            return False
        if button != 1:
            return False
        
        self.parent.get_focus()
        pos = self.parent_layer.camera.screen_to_world(pygame.mouse.get_pos())
        if self.parent.axis == bf.axis.HORIZONTAL:
            pos = pos[0]
        else:
            pos = pos[1]
        new_value = self.parent.position_to_value(pos)
        self.parent.set_value(new_value)
        self.do_on_click_down(button)
        return True

class Slider(Button):

    def __init__(self, text: str, default_value: float = 1.0) -> None:
        super().__init__(text, None)
        self.axis : bf.axis = bf.axis.HORIZONTAL
        self.gap: float | int = 0
        self.spacing: bf.spacing = bf.spacing.MANUAL
        self.modified_callback : Callable[[float],Any] = None
        self.meter: SliderMeter = SliderMeter()
        self.handle = SliderHandle()
        self.add(self.meter, self.handle)
        self.meter.set_debug_color(bf.color.RED)
        self.set_value(default_value, True)

    def set_tooltip_text(self, text):
        return super().set_tooltip_text(text)

    def set_fill_color(self,color)->Self:
        self.meter.content.set_color(color)
        return self
    
    def set_axis(self,axis:bf.axis)->Self:
        self.axis = axis
        self.meter.set_axis(axis)
        self.dirty_shape = True
        return self
    
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
            self.handle.set_tooltip_text(str(self.get_value()))
            self.meter.set_tooltip_text(str(self.get_value()))

        return self

    def get_value(self) -> float:
        return self.meter.get_value()

    def on_key_down(self, key):
        if super().on_key_down(key):
            return True
        if not self.is_enabled: 
            return False
        if self.axis == bf.axis.HORIZONTAL:
            if key == pygame.K_RIGHT:
                self.set_value(self.meter.get_value() + self.meter.step)
            elif key == pygame.K_LEFT:
                self.set_value(self.meter.get_value() - self.meter.step)
            else:
                return False
            return True
        else:
            if key == pygame.K_UP:
                self.set_value(self.meter.get_value() + self.meter.step)
            elif key == pygame.K_DOWN:
                self.set_value(self.meter.get_value() - self.meter.step)
            else:
                return False

            return True

    def do_on_click_down(self, button) -> None:
        if not self.is_enabled: 
            return
        if button == 1:
            self.get_focus()

    def value_to_position(self, value: float) -> float:
        """
        Converts a value to a position on the meter, considering the step size.
        """
        rect = self.meter.get_inner_rect()
        value_range = self.meter.get_range()
        value = round(value / self.meter.step) * self.meter.step
        position_ratio = (value - self.meter.min_value) / value_range
        if self.axis == bf.axis.HORIZONTAL:
            return (
                rect.left
                + (self.handle.rect.w / 2)
                + position_ratio * (rect.width - self.handle.rect.w)
            )
        else:
            return (
                rect.bottom
                - (self.handle.rect.h / 2)
                - position_ratio * (rect.height - self.handle.rect.h)
            )
            
    def position_to_value(self, position: float) -> float:
        """
        Converts a position on the meter to a value, considering the step size.
        """
        rect = self.meter.get_inner_rect()
        if self.axis == bf.axis.HORIZONTAL:
            if self.rect.w == self.handle.rect.w:
                position_ratio = 0
            else:
                handle_half = self.handle.rect.w // 2
                position = max(rect.left + handle_half, min(position, rect.right - handle_half))
                position_ratio = (position - rect.left - handle_half) / (
                    rect.width - self.handle.rect.w
                )
        else:
            if self.rect.h == self.handle.rect.h:
                position_ratio = 0
            else:
                handle_half = self.handle.rect.h // 2
                position = max(rect.top + handle_half, min(position, rect.bottom - handle_half))
                # Flip ratio vertically: bottom is min, top is max
                position_ratio = (rect.bottom - position - handle_half) / (
                    rect.height - self.handle.rect.h
                )

        value_range = self.meter.get_range()
        value = self.meter.min_value + position_ratio * value_range
        return round(value / self.meter.step) * self.meter.step

    def get_min_required_size(self) -> tuple[float, float]:
        """
        Calculates the minimum required size for the slider, considering the text, meter, and axis.

        Returns:
            tuple[float, float]: The width and height of the minimum required size.
        """
        gap = self.gap if self.text else 0
        text_width, text_height = self._get_text_rect_required_size() if self.text else (0, 0)
        meter_width, meter_height = self.meter.resolve_size(self.meter.get_min_required_size())

        if self.axis == bf.axis.HORIZONTAL:
            width = text_width + gap + meter_width 
            height = max(text_height, meter_height)
        else:
            width = max(text_width, meter_width)
            height = text_height + gap + meter_height

        height += self.unpressed_relief
        return self.expand_rect_with_padding((0, 0, width, height)).size

    def _build_composed_layout(self) -> None:
        """
        Builds the composed layout for the slider, including the meter and handle.
        This method adjusts the sizes and positions of the meter and handle based on the slider's axis,
        autoresize conditions, and spacing settings. It ensures the slider's components are properly aligned
        and sized within the slider's padded rectangle.
        """
        self.text_rect.size = self._get_text_rect_required_size()

        size_changed = False
        gap = self.gap if self.text else 0

        full_rect = self.text_rect.copy()


        # Resolve the meter's size based on the axis and autoresize conditions
        if self.axis == bf.axis.HORIZONTAL:
            meter_width,meter_height = self.meter.get_min_required_size()
            if not self.autoresize_w:
                meter_width = self.get_inner_width() - gap - self.text_rect.w 
            meter_width,meter_height = self.meter.resolve_size((meter_width,meter_height))

            full_rect.w = max(self.get_inner_width(), meter_width + (gap + self.text_rect.w if self.text else 0))
            self.meter.set_size((meter_width, meter_height))
            full_rect.h = max(meter_height, self.text_rect.h if self.text else meter_height)

        else:  # VERTICAL
            meter_width, meter_height = self.meter.get_min_required_size()
            if not self.autoresize_h:
                meter_height = self.get_inner_height() - gap - self.text_rect.h
            meter_width, meter_height = self.meter.resolve_size((meter_width, meter_height))

            full_rect.h =  meter_height + (gap + self.text_rect.h if self.text else 0)
            self.meter.set_size((meter_width, meter_height))
            full_rect.w = max(meter_width, self.text_rect.w if self.text else meter_width)


        # Inflate the rect by padding and resolve the target size
        full_rect.h += self.unpressed_relief
        inflated = self.expand_rect_with_padding((0, 0, *full_rect.size)).size

        target_size = self.resolve_size(inflated)


        # Update the slider's size if it doesn't match the target size
        if self.rect.size != target_size:
            self.set_size(target_size)
            size_changed = True

        # Adjust the handle size based on the meter's size
        if self.axis == bf.axis.HORIZONTAL:
            handle_size = self.meter.get_inner_height() 
            self.handle.set_size(self.handle.resolve_size((handle_size, handle_size)))
        else:
            handle_size = self.meter.get_inner_width() 
            self.handle.set_size(self.handle.resolve_size((handle_size, handle_size)))

        self._align_composed()
        return size_changed

    def _align_composed(self):

        if not self.text:
            self.text_rect.size = (0,0)
        full_rect = self.get_local_inner_rect()
        left_rect = self.text_rect
        right_rect = self.meter.rect.copy()



        if self.axis == bf.axis.HORIZONTAL:
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
            left_rect.centery = right_rect.centery = full_rect.centery

        else:  # VERTICAL
            gap = {
                bf.spacing.MIN: 0,
                bf.spacing.HALF: (full_rect.height - left_rect.height - right_rect.height) // 2,
                bf.spacing.MAX: full_rect.height - left_rect.height - right_rect.height,
                bf.spacing.MANUAL: self.gap
            }.get(self.spacing, 0)

            gap = max(0, gap)
            combined_height = left_rect.height + right_rect.height + gap

            group_y = {
                bf.alignment.TOP: full_rect.top,
                bf.alignment.MIDTOP: full_rect.top,
                bf.alignment.BOTTOM: full_rect.bottom - combined_height,
                bf.alignment.MIDBOTTOM: full_rect.bottom - combined_height,
                bf.alignment.CENTER: full_rect.centery - combined_height // 2
            }.get(self.alignment, full_rect.top)

            left_rect.y, right_rect.y = group_y, group_y + left_rect.height + gap
            left_rect.centerx = right_rect.centerx = full_rect.centerx

        # Push text to local, push shape to world
        self.text_rect = left_rect
        right_rect.move_ip(*self.rect.topleft)
        self.meter.set_position(*right_rect.topleft)

        # Position the handle based on the current value
        if self.axis == bf.axis.HORIZONTAL:
            self.handle.set_center(self.value_to_position(self.meter.value), self.meter.rect.centery)
        else:
            self.handle.set_center(self.meter.rect.centerx, self.value_to_position(self.meter.value))

    def _build_layout(self) -> None:
        return self._build_composed_layout()

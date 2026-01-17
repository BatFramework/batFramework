import batFramework as bf
import pygame
from .button import Button
from .meter import BarMeter
from .indicator import Indicator, DraggableWidget
from .shape import Shape
from .interactiveWidget import InteractiveWidget
from .syncedVar import SyncedVar
from decimal import Decimal
from typing import Callable, Any, Self

def round_to_step_precision(value, step):
    decimals = -Decimal(str(step)).as_tuple().exponent
    rounded = round(value, decimals)
    # Preserve int type if step is an int
    if isinstance(step, int) or (isinstance(step, float) and step.is_integer()):
        return int(rounded)
    return rounded

class SliderHandle(Indicator, DraggableWidget):
    def __init__(self,synced_var:SyncedVar):
        super().__init__()
        self.set_color(bf.color.CLOUD_SHADE)
        self.set_click_mask(1)
        self.synced_var = synced_var
        synced_var.bind(self,self._on_synced_var_update)

    def __str__(self) -> str:
        return "SliderHandle"

    def top_at(self, x, y):
        return Shape.top_at(self,x,y)

    def on_click_down(self, button, event=None):
        if button == 1:
            self.parent.get_focus()
            event.consumed = True
        super().on_click_down(button, event)

    def do_on_drag(self, drag_start, drag_end):
        if not self.parent:
            return
        super().do_on_drag(drag_start, drag_end)
        meter: SliderMeter = self.parent
        new_value = meter.position_to_value(self.rect.center)
        self._on_synced_var_update(new_value) # need to call this manually otherwise the order of update is fucked up and handle goes outside meter
        self.synced_var.value = new_value

    def _on_synced_var_update(self,value:float):
        meter: SliderMeter = self.parent
        self.set_center(*meter.value_to_position(value))
        self.rect.clamp_ip(meter.get_inner_rect())

    def set_size(self, size):
        super().set_size(size)
        if self.parent:
            self.parent.dirty_shape = True

    def on_exit(self):
        before = self.is_clicked_down
        super().on_exit()
        self.is_clicked_down = before

    def draw_focused(self, camera):
        return

class SliderMeter(BarMeter, InteractiveWidget):
    def __init__(self, min_value=0, max_value=1, step=0.1, synced_var: SyncedVar = None):
        super().__init__(min_value, max_value, step, synced_var)
        self.axis = bf.axis.HORIZONTAL
        self.handle = SliderHandle(synced_var=synced_var)
        self.add(self.handle)
        self.set_padding(0)
        self.set_debug_color(bf.color.RED)

    def get_focus(self) -> bool:
        res = super().get_focus()
        if res:
            return self.parent.get_focus()
        return False
    def __str__(self) -> str:
        return "SliderMeter"

    def set_tooltip_text(self, text):
        self.handle.set_tooltip_text(text)
        return super().set_tooltip_text(text)

    def get_min_required_size(self):
        size = [bf.FontManager().DEFAULT_FONT_SIZE] * 2 
        if self.axis == bf.axis.HORIZONTAL:
            size[0] = size[1] * 3
        else:
            size[1] = size[0] * 3
        return self.expand_rect_with_padding((0, 0, *size)).size

    def value_to_position(self, value: float) -> tuple[float, float]:
        rect = self.get_inner_rect()
        value_range = self.get_range()
        if self.snap : 
            value = round_to_step_precision(value, self.step)
        ratio = (value - self.min_value) / value_range if value_range else 0

        if self.direction in [bf.direction.LEFT, bf.direction.DOWN]:
            ratio = 1 - ratio

        if self.axis == bf.axis.HORIZONTAL:
            x = rect.left + (self.handle.rect.w / 2) + ratio * (rect.width - self.handle.rect.w)
            y = rect.centery
        else:
            x = rect.centerx
            y = rect.bottom - (self.handle.rect.h / 2) - ratio * (rect.height - self.handle.rect.h)
        return (x, y)

    def position_to_value(self, position: tuple[float, float]) -> float:
        rect = self.get_inner_rect()
        if self.axis == bf.axis.HORIZONTAL:
            pos = position[0]
            handle_half = self.handle.rect.w / 2
            pos = max(rect.left + handle_half, min(pos, rect.right - handle_half))
            ratio = (pos - rect.left - handle_half) / (rect.width - self.handle.rect.w) if rect.width != self.handle.rect.w else 0
        else:
            pos = position[1]
            handle_half = self.handle.rect.h / 2
            pos = max(rect.top + handle_half, min(pos, rect.bottom - handle_half))
            ratio = (rect.bottom - pos - handle_half) / (rect.height - self.handle.rect.h) if rect.height != self.handle.rect.h else 0

        if self.direction in [bf.direction.LEFT, bf.direction.DOWN]:
            ratio = 1 - ratio

        value = self.min_value + ratio * self.get_range()
        return round_to_step_precision(value, self.step) if self.snap else value


    def handle_event(self, event: pygame.Event):


        if (self.is_hovered or getattr(self.parent, 'is_hovered', False) or self.handle.is_hovered) :
            if event.type in [pygame.MOUSEBUTTONUP,pygame.MOUSEBUTTONDOWN] and event.button in [4,5]:
                event.consumed = True
            elif event.type == pygame.MOUSEWHEEL:
                keys = pygame.key.get_pressed()
                shift_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
                is_vertical = self.axis == bf.axis.VERTICAL
                is_horizontal = not is_vertical
                if (not shift_held and is_horizontal) or (shift_held and is_vertical):
                    return
                if event.y:
                    delta = -self.step if event.y < 0 else self.step
                    if self.direction in [bf.direction.DOWN,bf.direction.LEFT]:
                        delta*=-1
                    self.parent.set_value(self.parent.get_value() + delta)
                    event.consumed = True
        super().handle_event(event)

    def on_click_down(self, button: int,event=None):
        # old_consume = event.consumed
        if not self.parent.is_enabled:
            return
        super().on_click_down(button,event)
        # event.consumed = old_consume
        if button == 1:
            self.parent.get_focus()
            world_pos = self.parent_layer.camera.get_mouse_pos()
            if self.get_inner_rect().collidepoint(*world_pos):
                new_value = self.position_to_value(world_pos)
                self.set_value(new_value)
                self.handle.on_click_down(button,event)

    def on_click_up(self, button, event=None):
        super().do_on_click_up(button,event)

    def _build_content(self):
        super()._build_content()
        handle_size = self.get_inner_height() if self.axis == bf.axis.HORIZONTAL else self.get_inner_width()
        self.handle.set_size(self.handle.resolve_size((handle_size, handle_size)))
        self.handle._on_synced_var_update(self.synced_var.value)


class Slider(Button):
    def __init__(self, text: str, default_value: float = 1.0, synced_var: SyncedVar = None) -> None:
        super().__init__(text, None)
        self.old_key_repeat = (0, 0)
        self.synced_var = synced_var or SyncedVar(default_value)
        self.axis: bf.axis = bf.axis.HORIZONTAL
        self.gap: float | int = 0
        self.spacing: bf.spacing = bf.spacing.MANUAL
        self.modify_callback: Callable[[float], Any] = None
        self.meter: SliderMeter = SliderMeter(synced_var=self.synced_var)
        self.add(self.meter)
        self.synced_var.bind(self, self._on_synced_var_update)
        self.set_range(0, self.synced_var.value)
        self.synced_var.update_bound_entities()

    def set_snap(self,snap:bool)->Self:
        self.meter.set_snap(snap)
        return self

    def do_on_get_focus(self) -> None:
        super().do_on_get_focus()
        self.old_key_repeat = pygame.key.get_repeat()
        pygame.key.set_repeat(200, 50)

    def do_on_lose_focus(self) -> None:
        super().do_on_lose_focus()
        pygame.key.set_repeat(*self.old_key_repeat)

    def _on_synced_var_update(self, value):
        if self.modify_callback:
            self.modify_callback(value)
        rounded = round_to_step_precision(self.get_value(), self.meter.step)
        self.meter.set_tooltip_text(str(rounded))

    def set_fill_color(self, color) -> Self:
        self.meter.content.set_color(color)
        return self

    def set_axis(self, axis: bf.axis) -> Self:
        self.axis = axis
        self.meter.axis = axis
        self.dirty_shape = True
        return self

    def set_direction(self, direction: bf.direction) -> Self:
        self.meter.set_direction(direction)
        self.set_axis(self.meter.axis)
        return self

    def set_visible(self, value: bool) -> Self:
        self.meter.set_visible(value)
        return super().set_visible(value)

    def __str__(self) -> str:
        return "Slider"

    def set_gap(self, value: int | float) -> Self:
        self.gap = max(0, value)
        return self

    def set_spacing(self, spacing: bf.spacing) -> Self:
        if spacing != self.spacing:
            self.spacing = spacing
            self.dirty_shape = True
        return self

    def set_modify_callback(self, callback: Callable[[float], Any]) -> Self:
        self.modify_callback = callback
        return self

    def set_range(self, range_min: float, range_max: float) -> Self:
        self.meter.set_range(range_min, range_max)
        # self.meter.set_value(self.synced_var.value)
        self.dirty_shape = True
        return self

    def set_step(self, step: float) -> Self:
        self.meter.set_step(step)
        self.dirty_shape = True
        return self

    def set_value(self, value) -> Self:
        value = max(self.meter.min_value, min(value, self.meter.max_value))
        self.synced_var.value = value
        return self

    def get_value(self) -> float:
        return self.synced_var.value

    def on_key_down(self, key, event):
        super().on_key_down(key, event)
        if event.consumed or not self.is_enabled:
            return

        step = self.meter.step
        value = self.get_value()
        axis = self.axis
        direction = self.meter.direction

        if axis == bf.axis.HORIZONTAL:
            if key == pygame.K_RIGHT:
                delta = step if direction == bf.direction.RIGHT else -step
            elif key == pygame.K_LEFT:
                delta = -step if direction == bf.direction.RIGHT else step
            else:
                return
        elif axis == bf.axis.VERTICAL:
            if key == pygame.K_UP:
                delta = step if direction == bf.direction.UP else -step
            elif key == pygame.K_DOWN:
                delta = -step if direction == bf.direction.UP else step
            else:
                return
        else:
            return

        self.set_value(value + delta)
        event.consumed = True


    def get_min_required_size(self) -> tuple[float, float]:
        left = self.text_widget.get_min_required_size()
        right = self.meter.get_min_required_size()
        gap = self.gap if self.text_widget.text else 0
        full_rect = pygame.FRect(0, 0, left[0] + right[0] + gap, left[1])
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
        gap = self.gap if self.spacing == bf.spacing.MANUAL else 0
        if self.meter.axis==bf.axis.HORIZONTAL:
            meter_width = self.get_inner_width() - self.text_widget.rect.w - gap
            meter_height = min(self.meter.get_min_required_size()[1], self.text_widget.rect.h)
        else:
            meter_height = self.get_inner_height()
            meter_width = min(self.text_widget.rect.h,max(self.meter.get_min_required_size()[0],self.get_inner_width() - self.text_widget.rect.w - gap))

        meter_size = self.meter.resolve_size((meter_width, meter_height))
        self.meter.set_size(meter_size)
        self._align_composed(self.text_widget, self.meter)
        return res

import batFramework as bf
import pygame


from .widgetUtils import LayoutSlot, distribute_horizontal, distribute_vertical
from .button import Button
from .meter import BarMeter
from .indicator import Indicator, DraggableWidget
from .shape import Shape
from .interactiveWidget import InteractiveWidget
from .interactiveShape import InteractiveShape
from .syncedVar import SyncedVar
from typing import Callable, Any, Self
from math import ceil



class SliderHandle(Indicator, DraggableWidget):
    def __init__(self, synced_var: SyncedVar):
        super().__init__()
        self.set_color(bf.color.CLOUD_SHADE)
        self.set_click_mask(1)
        self.synced_var = synced_var
        synced_var.bind(self, self._on_synced_var_update)
        self.set_debug_color("magenta")

    def __str__(self) -> str:
        return "SliderHandle"

    def top_at(self, x, y):
        return Shape.top_at(self, x, y)

    def on_click_down(self, button, event=None):
        if button == 1:
            self.parent.ask_focus()
            event.consumed = True
        super().on_click_down(button, event)

    def do_on_drag(self, drag_start, drag_end):
        if not self.parent or not self.is_enabled:
            return
        super().do_on_drag(drag_start, drag_end)
        meter: SliderMeter = self.parent
        new_value = meter.position_to_value(self.rect.center)
        self._on_synced_var_update(
            new_value
        )  # need to call this manually otherwise the order of update is fucked up and handle goes outside meter
        self.synced_var.value = new_value

    def _on_synced_var_update(self, value: float):
        self.update_position(value)


    def update_position(self, value: float=None)->Self:
        if value is None:
            value = self.synced_var.value
        meter: SliderMeter = self.parent
        r = self.rect.copy()
        r.center = meter.value_to_position(value)
        self.set_center(*r.clamp(meter.get_inner_rect()).center)
        

    def on_exit(self):
        before = self.is_clicked_down
        super().on_exit()
        self.is_clicked_down = before

    def draw_focused(self, camera):
        return

    def apply_post_updates(self, skip_draw: bool = False):
        should_update = self.dirty_shape
        super().apply_post_updates(skip_draw)
        if should_update: self.update_position()

class SliderMeter(BarMeter, InteractiveShape):
    def __init__(
        self, min_value=0, max_value=1, step=0.1, synced_var: SyncedVar = None
    ):
        self.handle = SliderHandle(synced_var=synced_var)
        super().__init__(min_value, max_value, step, synced_var)
        self.set_debug_color("black")
        self.set_padding(2)
        self.set_autoresize(True)
        self.add(self.handle)

    def enable(self)->Self:
        super().enable()
        self.handle.enable()
        return self

    def disable(self)->Self:
        super().disable()
        self.handle.disable()
        return self

    def ask_focus(self, focus_area:pygame.Rect=None) -> bool:
        res = super().ask_focus(focus_area)
        if res and isinstance(self.parent, InteractiveWidget):
            return self.parent.ask_focus(focus_area)
        return False

    def __str__(self) -> str:
        return "SliderMeter"

    def set_tooltip_text(self, text):
        self.handle.set_tooltip_text(text)
        return super().set_tooltip_text(text)

    def get_min_required_size(self):
        if not self.parent.text: 
            size = list(super().get_min_required_size())
        else:
            size = [max(bf.FontManager().DEFAULT_FONT_SIZE // 2, 12)] * 2
            
        if self.axis == bf.axis.HORIZONTAL:
            size[0] = size[1] * 3
        else:
            size[1] = size[0] * 3
        return self.expand_rect_with_padding((0, 0, *size)).size

    def value_to_position(self, value: float) -> tuple[float, float]:
        rect = self.get_inner_rect()
        value_range = self.get_range()
        if self.snap:
            value = bf.utils.round_to_step_precision(value, self.step)
        ratio = (value - self.min_value) / value_range if value_range else 0

        if self.direction in [bf.direction.LEFT, bf.direction.DOWN]:
            ratio = 1 - ratio

        if self.axis == bf.axis.HORIZONTAL:
            x = rect.left + (self.handle.rect.w / 2) + ratio * (rect.width - self.handle.rect.w)
            y = rect.centery
        else:
            x = rect.centerx
            y = (
                rect.bottom
                - (self.handle.rect.h / 2)
                - ratio * (rect.height - self.handle.rect.h)
            )
        return (x, y)

    def position_to_value(self, position: tuple[float, float]) -> float:
        rect = self.get_inner_rect()
        if self.axis == bf.axis.HORIZONTAL:
            pos = position[0]
            handle_half = self.handle.rect.w / 2
            pos = max(rect.left + handle_half, min(pos, rect.right - handle_half))
            ratio = (
                (pos - rect.left - handle_half) / (rect.width - self.handle.rect.w)
                if rect.width > self.handle.rect.w
                else 0
            )
        else:
            pos = position[1]
            handle_half = self.handle.rect.h / 2
            pos = max(rect.top + handle_half, min(pos, rect.bottom - handle_half))
            ratio = (
                (rect.bottom - pos - handle_half) / (rect.height - self.handle.rect.h)
                if rect.height > self.handle.rect.h
                else 0
            )

        if self.direction in [bf.direction.LEFT, bf.direction.DOWN]:
            ratio = 1 - ratio

        value = self.min_value + ratio * self.get_range()
        return bf.utils.round_to_step_precision(value, self.step) if self.snap else value


    def handle_event(self, event: pygame.Event):

        if self.is_enabled and (
            self.is_hovered
            or getattr(self.parent, "is_hovered", False)
            or self.handle.is_hovered
        ):
            if event.type in [
                pygame.MOUSEBUTTONUP,
                pygame.MOUSEBUTTONDOWN,
            ] and event.button in [4, 5]:
                event.consumed = True
            elif event.type == pygame.MOUSEWHEEL:
                keys = pygame.key.get_pressed()
                shift_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
                is_vertical = self.axis == bf.axis.VERTICAL
                is_horizontal = not is_vertical
                if (not shift_held and is_horizontal) or (shift_held and is_vertical):
                    return
                if event.y:
                    delta = -1  if event.y < 0 else 1
                    if self.direction in [bf.direction.DOWN, bf.direction.LEFT]:
                        delta *= -1
                    delta *= self.step if self.step > 0 else 1
                    self.parent.set_value(self.parent.get_value() + delta)

                    event.consumed = True
        super().handle_event(event)

    def on_click_down(self, button: int, event=None):
        # old_consume = event.consumed
        super().on_click_down(button, event)
        # event.consumed = old_consume
        if button == 1:
            if not self.parent.ask_focus(): return
            world_pos = self.parent_layer.camera.get_mouse_pos()
            if self.get_inner_rect().collidepoint(*world_pos):
                new_value = self.position_to_value(world_pos)
                self.set_value(new_value)
                self.handle.on_click_down(button, event)

    def build(self):
        changed = super().build()
        self._build_content()
        return changed

    def _build_content(self):
        super()._build_content()
        handle_size = (
            self.get_inner_height()
            if self.axis == bf.axis.HORIZONTAL
            else self.get_inner_width()
        )
        self.handle.set_size(self.handle.resolve_size((handle_size, handle_size)))


class Slider(Button):
    def __init__(
        self, text: str, default_value: float = 1.0, synced_var: SyncedVar = None
    ) -> None:
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

    def set_snap(self, snap: bool) -> Self:
        self.meter.set_snap(snap)
        return self

    def disable(self):
        self.meter.disable()
        return super().disable()

    def enable(self):
        self.meter.enable()
        return super().enable()

    def get_debug_outlines(self):
        yield from super().get_debug_outlines()

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
        rounded = bf.utils.round_to_step_precision(self.get_value(), self.meter.step)
        self.meter.set_tooltip_text(str(rounded))

    def set_fill_color(self, color) -> Self:
        self.meter.content.set_color(color)
        return self

    def set_axis(self, axis: bf.axis) -> Self:
        self.meter.set_axis(axis)
        self.axis = self.meter.axis
        self.dirty_shape = True
        return self

    def set_direction(self, direction: bf.direction) -> Self:
        self.meter.set_direction(direction)
        self.set_axis(self.meter.axis)
        return self

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
        self.dirty_shape = True
        return self

    def set_step(self, step: float) -> Self:
        self.meter.set_step(step)
        self.dirty_shape = True
        return self

    def set_value(self, value) -> Self:
        self.meter.set_value(value)
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
        text_size = self.renderer.get_min_size(
            self._build_style(),
        )

        meter_size = self.meter.resolve_size(self.meter.get_min_required_size())

        gap = self.gap if self.text else 0
        if self.axis == bf.axis.HORIZONTAL:
            width = text_size[0] + meter_size[0] + gap
            height = max(text_size[1], meter_size[1])
        else:
            width = max(text_size[0], meter_size[0])
            height = text_size[1] + meter_size[1] + gap

        full_rect = pygame.FRect(0, 0, width, height)
        full_rect.h += self.unpressed_relief

        return self.expand_rect_with_padding((0, 0, *full_rect.size)).size

    def _is_label_first(self) -> bool:
        """
        Returns True if label should be placed before the meter
        in layout order (min-value side).
        """
        if self.axis == bf.axis.HORIZONTAL:
            return self.meter.direction == bf.direction.RIGHT
        else:
            return self.meter.direction == bf.direction.DOWN

    def _compute_max_gap(
        self,
        inner_len: float,
        text_len: float,
        meter_len: float,
    ) -> float:
        """
        When spacing == MAX, all leftover space is converted into gap.
        """
        return max(0.0, inner_len - text_len - meter_len)



    def build(self) -> bool:
        res = super().build()

        # ---- Measure ------------------------------------------------
        text_w, text_h = self.get_text_size()
        meter_min_w, meter_min_h = self.meter.resolve_size(self.meter.get_min_required_size())

        local_inner = self.get_local_inner_rect()

        has_text = bool(self.text)

        # ---- Gap ----------------------------------------------------

        if not has_text:
            gap = 0
        elif self.spacing == bf.spacing.MANUAL:
            gap = self.gap
        elif self.spacing == bf.spacing.MIN:
            gap = 0
        elif self.spacing == bf.spacing.HALF:
            if self.axis == bf.axis.HORIZONTAL:
                gap = self._compute_max_gap(local_inner.width, text_w, meter_min_w) /2
            else:
                gap = self._compute_max_gap(local_inner.height, text_h, meter_min_h)/2
        elif self.spacing == bf.spacing.MAX:
            if self.axis == bf.axis.HORIZONTAL:
                gap = self._compute_max_gap(local_inner.width, text_w, meter_min_w)
            else:
                gap = self._compute_max_gap(local_inner.height, text_h, meter_min_h)
        else:
            gap = 0

        # ---- Slot weights ------------------------------------------
        meter_weight = 1 if (self.spacing in (bf.spacing.MANUAL, bf.spacing.MIN) or not has_text) else 0

        text_slot = LayoutSlot(size=(text_w, text_h), weight=0)
        meter_slot = LayoutSlot(size=(meter_min_w, meter_min_h), weight=meter_weight)

        # ---- Slot order (min-value side first) ---------------------
        if has_text:
            if self._is_label_first():
                slots = [text_slot, meter_slot]
            else:
                slots = [meter_slot, text_slot]
        else:
            slots = [meter_slot]

        # ---- Distribute --------------------------------------------
        if self.axis == bf.axis.HORIZONTAL:
            rects = distribute_horizontal(
                slots=slots,
                rect=local_inner,
                gap=gap,
                alignment=self.alignment,
            )
        else:
            rects = distribute_vertical(
                slots=slots,
                rect=local_inner,
                gap=gap,
                alignment=self.alignment,
            )

        # ---- Identify rects ----------------------------------------
        if has_text:
            if self._is_label_first():
                text_rect, meter_rect = rects
            else:
                meter_rect, text_rect = rects
        else:
            meter_rect = rects[0]

        # ---- Text positioning (LOCAL surface coords) ---------------
        if has_text:
            tx = ceil(text_rect.left)
            ty = ceil(text_rect.top)

            # Center text along the cross-axis within its slot
            if self.axis == bf.axis.HORIZONTAL:
                ty = ceil(text_rect.centery - text_h / 2)
            else:
                tx = ceil(text_rect.centerx - text_w / 2)

            self.text_rect.update(tx, ty, text_w, text_h)

        # ---- Meter size --------------------------------------------
        meter_size = meter_rect.size
        self.meter.set_size(meter_size)

        # ---- Meter position (WORLD coords) -------------------------
        self.meter.set_position(
            x=meter_rect.left + self.rect.x,
            y=meter_rect.top + self.rect.y,
        )

        return res
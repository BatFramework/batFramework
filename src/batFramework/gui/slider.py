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


class SliderMeter(Meter, InteractiveWidget):
    def __str__(self) -> str:
        return "SliderMeter"

    def __init__(self, min_value = 0, max_value = 1, step = 0.1):
        super().__init__(min_value, max_value, step)
        self.set_padding(0)

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

    # def apply_updates(self,skip_draw:bool=False):
    #     if self.dirty_constraints:
    #         self.resolve_constraints()  # Finalize positioning based on final size
    #         self.dirty_constraints = False

    #     # Build shape if needed
    #     if self.dirty_shape:
    #         self.build()  # Finalize widget size
    #         self.dirty_shape = False
    #         self.dirty_surface = True
    #         self.dirty_constraints = True
    #         # Propagate dirty_constraints to children in case size affects their position
    #         for child in self.children:
    #             child.dirty_constraints = True
    #         self.parent.dirty_shape = True
    #     # Resolve constraints now that size is finalized
    #     if self.dirty_constraints:
    #         self.resolve_constraints()  # Finalize positioning based on final size
    #         self.dirty_constraints = False


    #     # Step 3: Paint the surface if flagged as dirty
    #     if self.dirty_surface and not skip_draw:
    #         self.paint()
    #         self.dirty_surface = False



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
        # self.meter.set_tooltip_text(text)
        # self.handle.set_tooltip_text(text)
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
        if not self.is_enabled(): 
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
        rect = self.meter.get_padded_rect()
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
        gap = self.gap if self.text else 0
        if not self.text_rect:
            self.text_rect.size = self._get_text_rect_required_size()
        if not self.text : self.text_rect.w = 0
        w, h = self.text_rect.size
        h+=self.unpressed_relief
        if self.axis == bf.axis.HORIZONTAL:

            return self.inflate_rect_by_padding((0, 0, w + gap + self.meter.get_min_required_size()[0], h)).size
        else:
            return self.inflate_rect_by_padding((0, 0, w, h+ gap + self.meter.get_min_required_size()[1])).size
        
    def _build_composed_layout(self, other: Shape) -> bool:
        """
        Builds the layout for the slider, ensuring that child elements (handle and meter)
        are only resized after the slider's size is confirmed to be correct.
        """
        gap = self.gap if self.text else 0
        if not self.text:
            self.text_rect.w = 0

        # Step 1: Calculate the required size for the slider
        full_rect = self.text_rect.copy()

        if self.axis == bf.axis.HORIZONTAL:
            other_height = min(self.text_rect.h, self.font_object.get_height() + 1)
            full_rect.w += self.meter.get_min_required_size()[0] + gap
            full_rect.h = max(full_rect.h, other_height) + self.unpressed_relief
        else:  # VERTICAL
            other_width = self.text_rect.h
            full_rect.h += self.meter.get_min_required_size()[1] + gap
            full_rect.w = max(full_rect.w, other_width)
            full_rect.h += self.unpressed_relief

        # Step 2: Inflate the rect by padding and resolve the target size
        inflated = self.inflate_rect_by_padding((0, 0, *full_rect.size)).size
        target_size = self.resolve_size(inflated)

        # Step 3: If the slider's size is not confirmed, update it and return
        if self.rect.size != target_size:
            self.set_size(target_size)
            self.apply_post_updates(skip_draw=True)
            return

        # Step 4: Update the sizes of child elements (handle and meter) only after the slider's size is confirmed
        if self.axis == bf.axis.HORIZONTAL:
            other_height = min(self.text_rect.h, self.font_object.get_height() + 1)
            self.meter.set_size(self.meter.resolve_size((self.get_padded_width() - self.text_rect.w - gap, other_height)))
            self.handle.set_size(self.handle.resolve_size((other_height, other_height)))
        else:  # VERTICAL
            other_width = self.text_rect.h
            self.meter.set_size(self.meter.resolve_size((other_width, self.get_padded_height() - self.text_rect.h - gap)))
            self.handle.set_size(self.handle.resolve_size((other_width, other_width)))

        # Step 5: Align the composed elements
        self._align_composed(other)

        # Step 6: Position the handle based on the current value
        if self.axis == bf.axis.HORIZONTAL:
            self.handle.set_center(self.value_to_position(self.meter.value), self.meter.rect.centery)
        else:
            self.handle.set_center(self.meter.rect.centerx, self.value_to_position(self.meter.value))


    def _align_composed(self, other: Shape):
        full_rect = self.get_local_padded_rect()
        left_rect = self.text_rect
        right_rect = other.rect.copy()

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
        other.set_position(*right_rect.topleft)

    def _build_layout(self) -> None:
        self.text_rect.size = self._get_text_rect_required_size()
        self._build_composed_layout(self.meter)




    def apply_pre_updates(self):
        # Step 1: Constraints and shape/size
        super().apply_pre_updates()
        # Build text rect size
        self.text_rect.size = self._get_text_rect_required_size()
        # Compose layout for meter (but not handle position yet)
        self._build_composed_layout(self.meter)
        # Meter and handle may need to update their own pre-updates
        self.meter.apply_pre_updates()
        self.handle.apply_pre_updates()


    def apply_post_updates(self, skip_draw: bool = False):
        # Step 2: Final alignment and painting
        super().apply_post_updates(skip_draw=skip_draw)
        # Align handle to value (now that sizes are final)
        self._align_composed(self.meter)
        self.handle.apply_post_updates(skip_draw=skip_draw)
        self.meter.apply_post_updates(skip_draw=skip_draw)
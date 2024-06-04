import batFramework as bf
from .meter import Meter
from .button import Button
from .indicator import *
from .meter import Meter
from .shape import Shape
from .interactiveWidget import InteractiveWidget

class SliderHandle(Indicator, DraggableWidget):

    def on_click_down(self, button: int) -> None:
        super().on_click_down(button)
        if button == 1:
            self.parent.get_focus()

    def on_exit(self) -> None:
        self.is_hovered = False
        self.do_on_exit()

    def do_on_drag(self, x, y, world_drag_point) -> None:
        m = self.parent.meter
        r = m.get_padded_rect()
        position = self.rect.centerx
        self.rect.clamp_ip(r)
        # Adjust handle position to value
        self.parent.set_value(self.parent.position_to_value(position))

    def top_at(self, x, y):
        return Widget.top_at(self, x, y)


        
class SliderMeter(Meter,InteractiveWidget):
    def on_click_down(self,button:int)->None:
        if button == 1 : 
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
        self.modified_callback = None
        self.meter: SliderMeter = SliderMeter()
        self.handle =  SliderHandle().set_color(bf.color.CLOUD)
        self.add(self.meter,self.handle)
        self.meter.set_debug_color(bf.color.RED)
        self.set_value(default_value,True)
        
    def __str__(self) -> str:
        return "Slider"

    def set_gap(self, value: int | float) -> Self:
        value = max(0, value)
        self.gap = value
        return self

    def get_min_required_size(self) -> tuple[float, float]:
        if not self.text_rect:
            params = {
                "font_name": self.font_object.name,
                "text": self.text,
                "antialias": False,
                "color": "white",
                "bgcolor": "black",  # if (self.has_alpha_color() or self.draw_mode == bf.drawMode.TEXTURED) else self.color,
                "wraplength": int(self.get_padded_width()) if self.auto_wraplength else 0,
            }
            self.text_rect.size = self._render_font(params).get_size()
        w,h = self.text_rect.size
        return self.inflate_rect_by_padding(
            (0, 0, w + (self.gap if self.text else 0) + self.meter.rect.w, max(h, self.meter.rect.h))
        ).size



    def set_modify_callback(self, callback) -> Self:
        self.modified_callback = callback
        return self

    def set_range(self, range_min: float, range_max: float) -> Self:
        self.meter.set_range(range_min, range_max)
        return self

    def set_step(self, step: float) -> Self:
        self.meter.set_step(step)
        return self

    def set_value(self, value, no_callback: bool = False) -> Self:
        self.meter.set_value(value)
        self.dirty_shape = True
        if self.modified_callback and (not no_callback):
            self.modified_callback(self.meter.value)
        return self

    def do_on_key_down(self, key):
        if key == pygame.K_RIGHT:
            self.set_value(self.meter.get_value() + self.meter.step)
        elif key == pygame.K_LEFT:
            self.set_value(self.meter.get_value() - self.meter.step)
            
    def do_on_click_down(self, button) -> None:
        self.get_focus()


    def value_to_position(self, value: float) -> float:
        """
        Converts a value to a position on the meter, considering the step size.
        """
        rect = self.meter.get_padded_rect()
        value_range = self.meter.get_range()
        value = round(value / self.meter.step) * self.meter.step
        position_ratio = (value - self.meter.min_value) / value_range
        return rect.left + position_ratio * rect.width

        
    def position_to_value(self, position: float) -> float:
        """
        Converts a position on the meter to a value, considering the step size.
        """
        rect = self.meter.get_padded_rect()
        position = max(rect.left, min(position, rect.right))
        position_ratio = (position - rect.left) / rect.width
        value_range = self.meter.get_range()
        value = self.meter.min_value + position_ratio * value_range
        return round(value / self.meter.step) * self.meter.step

            

    def _build_layout(self) -> None:
        params = {
            "font_name": self.font_object.name,
            "text": self.text,
            "antialias": False,
            "color": "white",
            "bgcolor": "black",  # if (self.has_alpha_color() or self.draw_mode == bf.drawMode.TEXTURED) else self.color,
            "wraplength": int(self.get_padded_width()) if self.auto_wraplength else 0,
        }

        self.text_rect.size = self._render_font(params).get_size()
        
        gap = self.gap if self.text else 0
        
        if self.autoresize:
            meter_size =  self.text_rect.h * 10, self.text_rect.h
        else:
            meter_size = self.get_padded_width() - self.text_rect.w - gap,self.text_rect.h

        handle_size = meter_size[1],meter_size[1]

        tmp_rect = pygame.FRect(0,0,self.text_rect.w + gap + meter_size[0],self.text_rect.h)
        if self.autoresize:
            target_rect = self.inflate_rect_by_padding(tmp_rect)
            if self.rect.size != target_rect.size:
                self.set_size(target_rect.size)
                self.build()
                return

        # ------------------------------------ size is ok

        self.handle.set_size(handle_size)

        self.meter.set_size(meter_size)

        padded = self.get_padded_rect().move(-self.rect.x,-self.rect.y)
        
        self.align_text(tmp_rect,padded,self.alignment)
        self.text_rect.midleft = tmp_rect.midleft

        # place meter 

        self.meter.set_position(*self.text_rect.move(self.rect.x + gap,self.rect.y + (self.text_rect.h /2) - meter_size[1]/2).topright)

        # place handle

        r = self.meter.get_padded_rect()
        x = r[2] * self.meter.get_ratio()
        
        self.handle.set_center(r[0]+x,r.centery)

        # adjust handle if it is in max/min position so it doesn't overflow
        if self.handle.rect.left < r.left:
            self.handle.set_position(r.left,self.handle.rect.y)
        elif self.handle.rect.right > r.right:
            self.handle.set_position(r.right-self.handle.rect.w,self.handle.rect.y)

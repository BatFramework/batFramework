import batFramework as bf
from .meter import Meter
from .button import Button
from .indicator import *
from .meter import Meter
from .shape import Shape
from .interactiveWidget import InteractiveWidget

class SliderHandle(Indicator, DraggableWidget):

    def __str__(self) -> str:
        return "SliderHandle"

    def on_click_down(self, button: int) -> None:
        super().on_click_down(button)
        if button == 1:
            self.parent.get_focus()

    def on_exit(self) -> None:
        self.is_hovered = False
        self.do_on_exit()

    def do_on_drag(self,drag_start:tuple[float,float],drag_end: tuple[float,float]) -> None:
        super().do_on_drag(drag_start,drag_end)
        m : Meter = self.parent.meter
        r = m.get_padded_rect()
        position = self.rect.centerx
        self.rect.clamp_ip(r)
        # Adjust handle position to value
        new_value = self.parent.position_to_value(position)
        self.parent.set_value(new_value)
        self.rect.centerx = self.parent.value_to_position(new_value)

    def top_at(self, x, y):
        return Widget.top_at(self, x, y)


class SliderMeter(Meter,InteractiveWidget):

    def __str__(self) -> str:
        return "SliderMeter"

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
        self.spacing :bf.spacing = bf.spacing.MANUAL 
        self.modified_callback = None
        self.meter: SliderMeter = SliderMeter()
        self.handle =  SliderHandle().set_color(bf.color.CLOUD)
        self.add(self.meter,self.handle)
        self.meter.set_debug_color(bf.color.RED)
        self.set_value(default_value,True)
        # print(self.handle.rect)
        # self.handle.set_visible(False)
        
    def __str__(self) -> str:
        return "Slider"

    def set_gap(self, value: int | float) -> Self:
        value = max(0, value)
        self.gap = value
        return self

    def get_min_required_size(self) -> tuple[float, float]:
        gap = self.gap if self.text else 0
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
        return self.inflate_rect_by_padding((0, 0,w + gap + self.meter.rect.w,h)).size

    def set_spacing(self,spacing:bf.spacing)->Self:
        if spacing == self.spacing : return self
        self.spacing = spacing
        self.dirty_shape = True
        return self

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
        if self.meter.value != value :
            self.meter.set_value(value)
            self.dirty_shape = True
        if self.modified_callback and (not no_callback):
            self.modified_callback(self.meter.value)
        return self
    
    def get_value(self)->float:
        return self.meter.get_value()

    def do_on_key_down(self, key):
        if key == pygame.K_RIGHT:
            self.set_value(self.meter.get_value() + self.meter.step)
            bf.AudioManager().play_sound(self.click_down_sound)
        elif key == pygame.K_LEFT:
            self.set_value(self.meter.get_value() - self.meter.step)
            bf.AudioManager().play_sound(self.click_down_sound)
            
    def do_on_click_down(self, button) -> None:
        if button == 1 : self.get_focus()

    def value_to_position(self, value: float) -> float:
        """
        Converts a value to a position on the meter, considering the step size.
        """
        rect = self.meter.get_padded_rect()
        value_range = self.meter.get_range()
        value = round(value / self.meter.step) * self.meter.step
        position_ratio = (value - self.meter.min_value) / value_range
        # print(self.handle.rect)
        # print(rect.left + (self.handle.rect.w/2) + position_ratio * (rect.width - self.handle.rect.w),self.handle.rect.w,self.rect.right)
        return rect.left + (self.handle.rect.w/2) + position_ratio * (rect.width - self.handle.rect.w)

    def position_to_value(self, position: float) -> float:
        """
        Converts a position on the meter to a value, considering the step size.
        """
        handle_half = self.handle.rect.w/2
        rect = self.meter.get_padded_rect()
        position = max(rect.left + handle_half, min(position, rect.right - handle_half))

        position_ratio = (position - rect.left - handle_half) / (rect.width - self.handle.rect.w)
        value_range = self.meter.get_range()
        value = self.meter.min_value + position_ratio * value_range
        return round(value / self.meter.step) * self.meter.step

    def _build_layout(self) -> None:        

        gap = self.gap if self.text else 0

        params = {
            "font_name": self.font_object.name,
            "text": self.text,
            "antialias": False,
            "color": "white",
            "bgcolor": "black",  # if (self.has_alpha_color() or self.draw_mode == bf.drawMode.TEXTURED) else self.color,
            "wraplength": int(self.get_padded_width()) if self.auto_wraplength else 0,
        }

        self.text_rect.size = self._render_font(params).get_size()

        meter_size = [self.text_rect.h * 10, self.font_object.point_size]
        if not self.autoresize_w:
            meter_size[0] =  self.get_padded_width() - self.text_rect.w - gap

        tmp_rect = pygame.FRect(0,0,self.text_rect.w + gap + meter_size[0],self.text_rect.h)



        if self.autoresize_h or self.autoresize_w: 
            target_rect = self.inflate_rect_by_padding(tmp_rect)
            if not self.autoresize_w : target_rect.w = self.rect.w
            if not self.autoresize_h : target_rect.h = self.rect.h
            if self.rect.size != target_rect.size:
                self.set_size(target_rect.size)
                self.build()
                return

        # ------------------------------------ size is ok
        padded = self.get_padded_rect().move(-self.rect.x,-self.rect.y)

        self.meter.set_size_if_autoresize(meter_size)
        handle_size = 2*[self.meter.get_padded_height()]
        
        self.handle.set_size_if_autoresize(handle_size)

        self.align_text(tmp_rect,padded,self.alignment)
        self.text_rect.midleft = tmp_rect.midleft

        if self.text : 
            match self.spacing:
                case bf.spacing.MAX:
                    gap = padded.w - self.text_rect.w - self.meter.rect.w
                case bf.spacing.MIN:
                    gap = 0
                case bf.spacing.HALF:
                    gap = (padded.w)/2 - self.text_rect.w

        # place meter 

        self.meter.set_position(*self.text_rect.move(self.rect.x + gap,self.rect.y + (self.text_rect.h /2) - meter_size[1]/2).topright)
        # place handle

        # print(self.meter.rect.top - self.rect.top)
        # print(self.meter.rect.h)
        
        x = self.value_to_position(self.meter.value)
        r = self.meter.get_padded_rect()
        self.handle.set_center(x,r.centery)

        # self.handle.set_center(x,self.rect.top)


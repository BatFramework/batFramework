import batFramework as bf
from .meter import Meter
from .button import Button
from .indicator import *
from .meter import Meter


class SliderMeter(Meter,InteractiveWidget):

    def do_on_click_down(self, button: int) -> None:
        self.parent.get_focus()
        super().do_on_click_down(button)

    def on_mouse_motion(self, x, y) -> None:
        self.parent.handle.on_mouse_motion(x,y)
        if pygame.mouse.get_pressed()[0] :
            centerx = x- self.get_padded_left() - self.parent.handle.rect.w//2
            self.parent.set_value((centerx / self.parent.get_meter_active_width())* self.parent.meter.get_range())
            # self.build()

    # def top_at(self, x: float | int, y: float | int):
    #     res = super().top_at(x, y)
    #     if res == self.content : return self
class Slider(Button):
    def __init__(self, text: str, default_value: float = 1.0 ,callback=None) -> None:
        self.modified_callback = None
        self.meter : Meter = SliderMeter((20,4)).set_value(default_value)
        self.meter.set_debug_color(bf.color.RED)
        self.handle: SliderHandle = SliderHandle()
        self.handle.set_debug_color(bf.color.ORANGE)

        self.handle.disable_clip_to_parent()

        self.gap: float | int = 0
        super().__init__(text, callback)
        self.add_child(self.meter, self.handle)


    def to_string_id(self) -> str:
        return "Slider"

    def set_gap(self, value: int | float) -> Self:
        value = max(0,value)
        self.gap = value
        self.build()
        return self


    def on_mouse_motion(self, x, y) -> None:
        self.handle.on_mouse_motion(x,y)
        if self.get_root().get_hovered() == self and self.handle.clicked_inside:
            centerx = x- self.meter.get_padded_left() - self.handle.rect.w//2
            self.set_value((centerx / self.get_meter_active_width())* self.meter.get_range())


    def set_modify_callback(self,callback)->Self:
        self.modified_callback = callback
        return self


    def set_range(self,range_min:float,range_max:float)->Self:
        self.meter.set_range(range_min,range_max)
        self.build()
        return self
    
    def set_step(self,step:float)->Self:
        self.meter.set_step(step)
        self.build()
        return self

    def set_value(self,value,no_callback :bool = False)->Self:
        self.meter.set_value(value)
        self.build()
        if self.modified_callback and (not no_callback): self.modified_callback(self.meter.value)
        return self

    def do_on_key_down(self, key):
        if key == pygame.K_RIGHT:
            self.set_value(self.meter.get_value()+self.meter.step)
        elif key == pygame.K_LEFT:
            self.set_value(self.meter.get_value()-self.meter.step)
        else:
            return
        self.build()
    
    def get_meter_active_width(self)->float:
        return (self.meter.get_padded_width()-self.handle.rect.w)
    
    def get_relative_meter_value(self,x:float)->float:
        return self.get_meter_active_width()

    def get_relative_handle_position(self,value:float)->float:
        return self.get_meter_active_width() * (value / self.meter.get_range())

    def do_on_click_down(self, button) -> None:
        if not self.get_focus():return
    
    def build(self) -> None:
        self.meter.build()
        self.handle.build()
        super().build()
    
    def _build_layout(self) -> None:
        self.handle.set_size((self.text_rect.h,self.text_rect.h))
        size = (
            0,0,self.text_rect.w + self.meter.rect.w + self.gap,
            max(self.text_rect.h, self.meter.rect.h),
        )
        required_rect = self.inflate_rect_by_padding(size)

        if self.autoresize and (self.rect.size != required_rect.size):
            self.resized_flag = True
            self.set_size(required_rect.size)
            return
        elif not self.autoresize:
            self.meter.set_size((self.get_padded_width() -self.text_rect.w - self.gap,self.get_padded_height()))
        if self.resized_flag:
            self.resized_flag = False
            if self.parent:
                self.parent.notify()

        
        self.handle.set_size((self.meter.rect.h,self.meter.rect.h))
        
        
        # Adjust positions

        self.text_rect.midleft = self.get_padded_rect_rel().midleft
        meter_rect = self.meter.rect.copy()
        meter_rect.midleft = self.get_padded_rect().move(self.text_rect.w + self.gap, self.relief - self.get_relief()).midleft
        self.meter.set_position(*meter_rect.topleft)
        handle_rect = self.handle.rect.copy()
        handle_rect.center = self.meter.content.rect.midright
        handle_rect.right = min(self.meter.get_padded_right(),handle_rect.right)
        handle_rect.left = max(self.meter.get_padded_left(),handle_rect.left)

        self.handle.set_position(*handle_rect.topleft)
        l = []
        if self.show_text_outline : 
            l.append((self.text_outline_surface, self.text_rect.move(-1,self.relief - self.get_relief()-1)))
        l.append((self.text_surface, self.text_rect.move(0,self.relief - self.get_relief())))
        self.surface.fblits(l)
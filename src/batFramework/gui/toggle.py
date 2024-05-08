from .button import Button
from .indicator import Indicator, ToggleIndicator
import batFramework as bf
from typing import Self

class Toggle(Button):
    def __init__(self, text: str, default_value: bool = False,callback=None) -> None:
        self.value: bool = default_value
        self.indicator: ToggleIndicator = ToggleIndicator(default_value)
        self.indicator.disable_clip_to_parent()
        self.gap: float | int = 0
        super().__init__(text, callback)
        self.add_child(self.indicator)
        self.set_gap(int(max(4, self.get_padded_width() / 3)))

    def set_value(self,value:bool,do_callback=False)->Self:
        self.value = value
        self.indicator.set_value(value)
        self.build()
        if do_callback: self.callback(self.value)
        return self

    def click(self) -> None:
        if self.callback is not None:
            self.set_value(not self.value,True)
            bf.Timer(duration=0.3,end_callback=self._safety_effect_end).start()
        
    def set_gap(self, value: int | float) -> Self:
        value = max(0,value)
        self.gap = value
        self.build()
        return self

    def to_string_id(self) -> str:
        return f"Toggle({self.value})"

    def toggle(self) -> None:
        self.set_value(not self.value,do_callback = True)



    def get_min_required_size(self) -> tuple[float, float]:
        if not self.font_object : return (0,0)
        w,h = self.font_object.size(self.text)
        return self.inflate_rect_by_padding((0,0,w+self.gap+self.indicator.rect.w,max(h, self.indicator.rect.h))).size
        

    def _build_layout(self) -> None:
        h = self.get_padded_height()
        self.indicator.set_size((h,h))
        size = (
            0,0,self.text_rect.w + self.indicator.rect.w + self.gap,
            max(self.text_rect.h, self.indicator.rect.h),
        )
        required_rect = self.inflate_rect_by_padding(size)

        if self.autoresize and (self.rect.size != required_rect.size):
            self.resized_flag = True
            self.set_size(required_rect.size)
            return
        if self.resized_flag:
            self.resized_flag = False
            if self.parent:
                self.parent.notify()

        # Adjust positions
        self.text_rect.midleft = self.get_padded_rect_rel().midleft
        indicator_rect = self.indicator.rect.copy()
        indicator_rect.midleft = self.get_padded_rect().move(self.text_rect.w + self.gap, self.relief - self.get_relief()).midleft
        self.indicator.set_position(*indicator_rect.topleft)

        l = []
        if self.show_text_outline : 
            l.append((self.text_outline_surface, self.text_rect.move(-1,self.relief - self.get_relief()-1)))
        l.append((self.text_surface, self.text_rect.move(0,self.relief - self.get_relief())))
        self.surface.fblits(l)

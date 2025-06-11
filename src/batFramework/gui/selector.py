import batFramework as bf
import pygame
from typing import Self,Callable,Any
from .button import Button
from .indicator import ArrowIndicator
from .clickableWidget import ClickableWidget
from .widget import Widget

class MyArrow(ArrowIndicator,ClickableWidget):
    def top_at(self,x,y):
        return Widget.top_at(self,x,y)

    def get_focus(self):
        return self.parent.get_focus()

class Selector(Button):
    def __init__(self,options:list[str]=None,default_value:str=None,allow_cycle:bool=False):
        super().__init__('')
        self.allow_cycle = allow_cycle
        self.current_index = 0
        self.on_modify_callback : Callable[[str,int],Any] = None
        self.options = options if options else []
        self.gap : int = 2
        text_value = ""

        
        if not (default_value is not None and default_value in self.options): 
            default_value = options[0]
            
        text_value = default_value  
        self.current_index = self.options.index(default_value)

        self.left_indicator : MyArrow = (MyArrow(bf.direction.LEFT)
            .set_color((0,0,0,0)).set_arrow_color(self.text_color)
            .set_callback(lambda : self.set_by_index(self.get_current_index()-1))
        )

        self.right_indicator:MyArrow =(MyArrow(bf.direction.RIGHT)
            .set_color((0,0,0,0)).set_arrow_color(self.text_color)
            .set_callback(lambda : self.set_by_index(self.get_current_index()+1))
        )
        
        self.add(self.left_indicator,self.right_indicator)
        self.set_clip_children(False)
        self.set_text(text_value)

    def __str__(self):
        return f"Selector[{self.options[self.current_index]}]"

    def set_gap(self,value:int)->Self:
        self.gap = value
        self.dirty_shape = True
        return self
    
    def set_arrow_color(self,color)->Self:
        self.left_indicator.set_arrow_color(color)
        self.right_indicator.set_arrow_color(color)
        return self

    def disable(self):
        super().disable()
        self.left_indicator.disable()
        self.right_indicator.disable()
        return self
    
    def enable(self):
        super().enable()
        self.right_indicator.enable()
        self.left_indicator.enable()
        index = self.current_index
        if not self.allow_cycle:
            if index == 0:
                self.left_indicator.disable()
            else:
                self.left_indicator.enable()
            if index == len(self.options)-1:
                self.right_indicator.disable()
            else:
                self.right_indicator.enable()


        return self

    def set_tooltip_text(self, text):
        self.left_indicator.set_tooltip_text(text)
        self.right_indicator.set_tooltip_text(text)
        return super().set_tooltip_text(text)

    def get_min_required_size(self) -> tuple[float, float]:
        """
        Calculates the minimum size required for the selector, including text and indicators.
        """

        # Calculate the maximum size needed for the text
        old_text = self.text
        max_text_size = (0, 0)
        for option in self.options:
            self.text = option
            text_size = self._get_text_rect_required_size()
            max_text_size = max(max_text_size[0], text_size[0]), max(max_text_size[1], text_size[1])
        self.text = old_text

        # Ensure total_height is always an odd integer
        total_height = max(self.font_object.get_height()+1, max_text_size[1] * 1.5)
        total_height += self.unpressed_relief
        total_height += max(self.right_indicator.outline_width,self.left_indicator.outline_width)

        # Calculate total width and height
        total_width = (
            total_height*2+
            max_text_size[0] +  # Text width
            self.gap * 2      # Gaps between text and indicators
        )
        # Inflate by padding at the very end
        final_size = self.expand_rect_with_padding((0, 0, total_width, total_height)).size

        return final_size

    def _align_content(self):
        """
        Builds the selector layout (places and resizes the indicators)
        """

        # return
        # Step 1: Calculate the padded area for positioning
        padded = self.get_inner_rect()

    
        # left_size = self.left_indicator.rect.size
        right_size = self.right_indicator.rect.size

        indicator_height = padded.h

        self.left_indicator.set_size((indicator_height,indicator_height))
        self.right_indicator.set_size((indicator_height,indicator_height))


        # Step 3: Position indicators
        self.left_indicator.set_position(padded.left, None)
        self.left_indicator.set_center(None, padded.centery)

        self.right_indicator.set_position(padded.right - right_size[0], None)
        self.right_indicator.set_center(None, padded.centery)

    def apply_post_updates(self, skip_draw = False):
        super().apply_post_updates(skip_draw)
        self._align_content()

    def get_current_index(self)->int:
        return self.current_index

    def set_allow_cycle(self,value:bool)->Self:
        if value == self.allow_cycle: return self
        self.allow_cycle = value
        self.dirty_surface = True
        return self

    def set_text_color(self,color)->Self:
        super().set_text_color(color)
        self.left_indicator.set_arrow_color(color)
        self.right_indicator.set_arrow_color(color)
        return self

    def set_modify_callback(self,function:Callable[[str,int],Any]):
        """
        the function will receive the value and the index 
        """
        self.on_modify_callback = function
        return self

    def set_by_index(self,index:int)->Self:
        if self.allow_cycle:
            index = index%len(self.options)
        else:
            index = max(min(len(self.options)-1,index),0)
    
        if index == self.current_index:
            return self

        self.current_index = index
        self.set_text(self.options[self.current_index])
        if self.on_modify_callback:
            self.on_modify_callback(self.options[self.current_index],self.current_index)
        if not self.allow_cycle:
            if index == 0:
                self.left_indicator.disable()
            else:
                self.left_indicator.enable()
            if index == len(self.options)-1:
                self.right_indicator.disable()
            else:
                self.right_indicator.enable()
        return self

    def paint(self):
        super().paint()
        self.left_indicator.show()
        self.right_indicator.show()
        if not self.allow_cycle and self.current_index == 0:
            self.left_indicator.hide()
        elif not self.allow_cycle and self.current_index== len(self.options)-1:
            self.right_indicator.hide()
            
    def set_by_value(self,value:str)->Self:
        if not self.is_enabled : return
        if value not in self.options : return self
        index = self.options.index(value)
        self.set_by_index(index)
        return self

    def on_key_down(self, key: int) -> bool:
        if not self.is_enabled:
            return False

        key_actions = {
            pygame.K_RIGHT: self.right_indicator,
            pygame.K_SPACE: self.right_indicator,
            pygame.K_LEFT: self.left_indicator
        }

        indicator = key_actions.get(key)
        if indicator and indicator.visible and indicator.is_enabled:
            indicator.on_click_down(1)
            return True

        return False

    def on_key_up(self, key: int) -> bool:
        if not self.is_enabled:
            return False

        key_actions = {
            pygame.K_RIGHT: self.right_indicator,
            pygame.K_SPACE: self.right_indicator,
            pygame.K_LEFT: self.left_indicator
        }

        indicator = key_actions.get(key)
        if indicator and indicator.visible and indicator.is_enabled:
            indicator.on_click_up(1)
            return True

        return False
    
    def do_on_click_down(self, button) -> None:
        if self.is_enabled and button == 1:
            if not self.get_focus():
                return True
        return False


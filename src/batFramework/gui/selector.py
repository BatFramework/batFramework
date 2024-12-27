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
        self.allow_cycle = allow_cycle
        self.default_value = default_value
        self.current_index = 0
        self.on_modify_callback : Callable[[str,int],Any] = None 
        self.options = options if options else []
        self.gap : int = 2
        text_value = ""
        if default_value is None or default_value not in self.options: 
            self.default_value = options[0]
            text_value = self.default_value  
            self.current_index = self.options.index(self.default_value)

        super().__init__(text = text_value)
        self.left_indicator = (MyArrow(bf.direction.LEFT)
            .add_constraints(bf.gui.AnchorLeft(),bf.gui.CenterY(),bf.gui.FillY())
            .set_draw_stem(False)
            .set_color((0,0,0,0)).set_arrow_color(self.text_color)
            .set_callback(lambda : self.set_by_index(self.get_current_index()-1))
        )

        self.right_indicator=(MyArrow(bf.direction.RIGHT)
            .add_constraints(bf.gui.AnchorRight(),bf.gui.CenterY(),bf.gui.FillY())
            .set_draw_stem(False)
            .set_color((0,0,0,0)).set_arrow_color(self.text_color)
            .set_callback(lambda : self.set_by_index(self.get_current_index()+1))
        )
        
        self.add(self.left_indicator,self.right_indicator)
        self.set_clip_children(False)

    def set_gap(self,value:int)->Self:
        self.gap = value
        self.dirty_shape = True
        return self
        
    def get_min_required_size(self) -> tuple[float, float]:
        old_text = self.text
        res = self.text_rect.size if self.text_rect else self._get_text_rect_required_size()
        for option in self.options:
            self.text = option
            tmp = self.inflate_rect_by_padding(
                (0, 0, *self._get_text_rect_required_size())
            ).size
            res = max(res[0],tmp[0]),max(res[1],tmp[1])
        self.text = old_text


        res = res[0],res[1]+self.unpressed_relief
        
        min_right = self.right_indicator.get_min_required_size()[0]
        min_left =self.left_indicator.get_min_required_size()[0]
        if self.autoresize_w:
            res = (res[0] + self.gap*2 + min_left + min_right, res[1])
        
        return res[0] if self.autoresize_w else self.rect.w, (
            res[1] if self.autoresize_h else self.rect.h
        )

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
        if not self.enabled : return
        if value not in self.options : return self
        index = self.options.index(value)
        self.set_by_index(index)
        return self

    def do_on_key_down(self,key:int):
        if not self.enabled : return False
        if key == pygame.K_RIGHT or key == pygame.K_SPACE:
            if self.right_indicator.visible:
                self.right_indicator.do_on_click_down(1)
        elif key == pygame.K_LEFT:
            if self.left_indicator.visible:
                self.left_indicator.do_on_click_down(1)
        else:
            return False
        return True
        
    def do_on_key_up(self,key:int):
        if not self.enabled : return False
        if key == pygame.K_RIGHT or key == pygame.K_SPACE:
            if self.right_indicator.visible:
                self.right_indicator.do_on_click_up(1)
        elif key == pygame.K_LEFT:
            if self.left_indicator.visible:
                self.left_indicator.do_on_click_up(1)
        else: 
            return False
        return True
    def do_on_click_down(self, button) -> None:
        if self.enabled and button == 1:
            if not self.get_focus():
                return True
        return False
                

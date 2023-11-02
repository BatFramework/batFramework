from .label import Label
import batFramework as bf
from types import FunctionType
from .interactiveWidget import InteractiveWidget
import pygame
class Button(Label,InteractiveWidget):
    def __init__(self, text: str, callback : FunctionType =None) -> None:
        # Label.__init__(self,text) 
        self.callback = callback    
        self.click_action = bf.Action("click").add_mouse_control(1)
        self.hover_action = bf.Action("hover").add_mouse_control(pygame.MOUSEMOTION)
        self.is_hovered : bool = False
        self.is_clicking : bool = False
        super().__init__(text)


    def on_get_focus(self):
        super().on_get_focus()
        self.build()

    def on_lose_focus(self):
        super().on_lose_focus()
        self.build()

    def to_string_id(self)->str:
        return f"Button({self._text})"   

    def click(self)->None:
        if self.callback and not self.is_clicking:
            self.is_clicking = True
            self.callback()
            self.is_clicking = False
            
            
    def do_process_actions(self,event):
        self.click_action.process_event(event)
        self.hover_action.process_event(event)

    def do_reset_actions(self):
        self.click_action.reset()
        self.hover_action.reset()

    def do_handle_event(self,event)->None:
        res = False
        if self.click_action.is_active():
            root = self.get_root()
            if root.hovered ==  self:
                if not self.is_focused :  self.get_focus()
                self.click()
        elif self.hover_action.is_active():
            root = self.get_root()
            if root:
                if self.is_hovered and root.hovered != self:
                    self.is_hovered = False
                    self.build()
                if not self.is_hovered and root.hovered == self:
                    self.is_hovered = True
                    self.build()
        return res
        
    def build(self)->None:
        super().build()
        if self.is_hovered:
            hover_surf = pygame.Surface(self.surface.get_size()).convert_alpha()
            hover_surf.fill((80,80,80,0))
            self.surface.blit(hover_surf,(0,0),special_flags = pygame.BLEND_ADD)

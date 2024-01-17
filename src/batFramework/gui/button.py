from .label import Label
import batFramework as bf
from typing import Self,Callable
from .interactiveWidget import InteractiveWidget
import pygame


class Button(Label, InteractiveWidget):
    _cache = {}

    def __init__(self, text: str, callback: None| Callable = None) -> None:
        # Label.__init__(self,text)
        self.callback = callback
        self.click_action = bf.Action("click").add_mouse_control(1)
        self.hover_action = bf.Action("hover").add_mouse_control(pygame.MOUSEMOTION)
        self.is_hovered: bool = False
        self.is_clicking: bool = False
        self.effect_max :float= 20
        self.effect_speed :float= 1.2
        self.effect :float = 0
        self.enabled :bool = True
        super().__init__(text=text)
        self.set_debug_color("cyan")

    def get_surface_filter(self)->pygame.Surface|None:
        if not self.surface : return None
        size = self.surface.get_size()
        surface_filter = Button._cache.get(size, None)
        if surface_filter is None:
            surface_filter = pygame.Surface(size).convert_alpha()
            surface_filter.fill((30, 30, 30, 0))
            Button._cache[size] = surface_filter
        return surface_filter
    def enable(self)->Self:
        self.enabled = True
        self.build()
        return self

    def disable(self)->Self:
        self.enabled = False
        self.build()
        return self

    def is_enabled(self)->bool:
        return self.enabled

    def set_callback(self, callback: Callable) -> Self:
        self.callback = callback
        return self

    def on_get_focus(self):
        super().on_get_focus()
        self.build()

    def on_lose_focus(self):
        super().on_lose_focus()
        self.build()

    def to_string_id(self) -> str:
        return f"Button({self._text}){'' if self.enabled else '[disabled]'}"

    def click(self) -> None:
        if self.callback is not None and not self.is_clicking:
            self.is_clicking = True
            self.callback()
            self.is_clicking = False

    def start_effect(self):
        if self.effect <= 0 : self.effect = self.effect_max

    def do_process_actions(self, event):
        self.click_action.process_event(event)
        self.hover_action.process_event(event)

    def do_reset_actions(self):
        self.click_action.reset()
        self.hover_action.reset()

    def do_handle_event(self, event) -> bool:
        res = False
        if self.click_action.is_active():
            root = self.get_root()
            if root is None : return res
            if root.get_hovered() == self and self.enabled:
                if not self.is_focused:
                    self.get_focus()
                # self.click()
                self.start_effect()
                res = True
        elif self.hover_action.is_active():
            root = self.get_root()
            if root:
                if self.is_hovered and root.hovered != self:
                    self.is_hovered = False
                    self.build()
                    res = True
                if not self.is_hovered and root.hovered == self:
                    self.is_hovered = True
                    self.build()
                    res = True
        return res

    def update(self,dt):
        super().update(dt)
        if self.effect > 0:
            self.effect -= dt*60*self.effect_speed
            self.build()
            if self.effect <= 0:
                self.is_hovered = False
                self.effect = 0
                self.click()
                self.build()

    def _build_effect(self)->None:
        pygame.draw.rect(
            self.surface,
            bf.color.CLOUD_WHITE,
            (0,0,*self.surface.get_size()),
            int(self.effect),
            *self._border_radius
            )
                
    def build(self) -> None:
        super().build()
        size = self.surface.get_size()
        if not self.enabled:
            self.surface.blit(self.get_surface_filter(), (0, 0), special_flags=pygame.BLEND_SUB)
            return
        if self.effect:
            if self.effect >= 1 : 
                self._build_effect()
            return
        if self.is_hovered:
            self.surface.blit(self.get_surface_filter(), (0, 0), special_flags=pygame.BLEND_ADD)

    def apply_contraints(self) -> None:
        super().apply_constraints()


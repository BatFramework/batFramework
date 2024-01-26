from .label import Label
import batFramework as bf
from typing import Self,Callable
from .interactiveWidget import InteractiveWidget
import pygame


class Button(Label, InteractiveWidget):
    _cache :dict = {}

    def __init__(self, text: str, callback: None| Callable = None) -> None:
        # Label.__init__(self,text)
        self.callback = callback
        self.is_hovered: bool = False
        self.effect_max :float= 20
        self.effect_speed :float= 1.8
        self.is_clicking : bool = False
        self.effect :float = 0
        self.enabled :bool = True
        super().__init__(text=text)
        self.set_debug_color("cyan")
        self.focusable = True

    def get_surface_filter(self) -> pygame.Surface | None:
            if not self.surface:
                return None

            size = self.surface.get_size()
            surface_filter = Button._cache.get(size, None)

            if surface_filter is None:
                # Create a mask from the original surface
                mask = pygame.mask.from_surface(self.surface,threshold=0)

                # Get the bounding box of the mask
                silhouette_surface = mask.to_surface(
                    setcolor = (30,30,30),unsetcolor= (255,255,255)
                ).convert_alpha()
                

                Button._cache[size] = silhouette_surface
                surface_filter = silhouette_surface

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
        if self.callback is not None:
            self.callback()
            bf.Timer(duration=0.3,end_callback=self._safety_effect_end).start()

    def _safety_effect_end(self)->None:
        if self.effect > 0:
            self.effect = 0
            self.build()
                    
    def start_effect(self):
        if self.effect <= 0 : self.effect = self.effect_max


    def do_on_click_down(self,button)->None:
        if self.enabled and button == 1 and self.effect == 0:
            if not self.get_focus():return
            self.is_clicking = True
            self.start_effect()

    def do_on_click_up(self,button)->None:
        if self.enabled and button == 1 and self.is_clicking: 
            # self.effect = 0
            self.is_clicking = False
            self.build()
            self.click()
    
    def on_enter(self)->None:
        if not self.enabled : return
        super().on_enter()
        self.effect = 0
        self.build()
        pygame.mouse.set_cursor(*pygame.cursors.tri_left)

    def on_exit(self)->None:
        super().on_exit()
        # self.effect = 0
        self.is_clicking = False
        self.build()
        pygame.mouse.set_cursor(pygame.cursors.arrow)



    def update(self,dt):
        super().update(dt)
        if self.effect <= 0: return
        self.effect -= dt*60*self.effect_speed
        if self.is_clicking:
            if self.effect < 1 : self.effect = 1
        else:
            if self.effect < 0 : self.effect = 0
        self.build()

    def _build_effect(self)->None:
        if self.effect < 1 : return
        e = int(min(self.rect.w //3, self.rect.h//3,self.effect))
        pygame.draw.rect(
            self.surface,
            bf.color.CLOUD_WHITE,
            (0,0,*self.surface.get_size()),
            #int(self.effect),
            e,
            *self._border_radius
            )
    def _build_disabled(self)->None:
        self.surface.blit(self.get_surface_filter(), (0, 0), special_flags=pygame.BLEND_SUB)

    def _build_hovered(self)->None:
        self.surface.blit(self.get_surface_filter(), (0, 0), special_flags=pygame.BLEND_ADD)

    def build(self) -> None:
        super().build()
        if not self.enabled:
            self._build_disabled()
        elif self.is_hovered:
            self._build_hovered()
        if self.effect:
            self._build_effect()

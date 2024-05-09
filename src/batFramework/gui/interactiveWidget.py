from .widget import Widget
from typing import Self
from typing import TYPE_CHECKING
import pygame
if TYPE_CHECKING:
    from .container import Container
import batFramework as bf

class InteractiveWidget(Widget):
    def __init__(self, *args, **kwargs)->None:
        self.is_focused: bool = False
        self.is_hovered: bool = False
        self.is_clicked_down:bool = False
        self.focused_index = 0
        super().__init__(convert_alpha=True)
        self.focusable = True

    def set_focusable(self,value:bool)->Self:
        self.focusable = value
        return self
    

    def allow_focus_to_self(self)->bool:
        return True

    def get_focus(self) -> bool:
        if self.focusable and ((r:=self.get_root()) is not None):
            r.focus_on(self)
            if self.parent and isinstance(self.parent,InteractiveWidget): 
                self.parent.set_focused_child(self)
            return True
        return False

    def lose_focus(self) -> bool:
        if self.is_focused  and ((r:=self.get_root()) is not None):
            r.focus_on(None)
            return True
        return False
        
    def on_get_focus(self) -> None:
        self.is_focused = True
        self.do_on_get_focus()

    def on_lose_focus(self) -> None:
        self.is_focused = False
        self.do_on_lose_focus()

    def on_key_down(self,key):
        if key == pygame.K_DOWN or key == pygame.KMOD_ALT:
            self.focus_next_sibling()
        if key == pygame.K_UP:
            self.focus_prev_sibling()
        self.do_on_key_down(key)

    def on_key_up(self,key):
        self.do_on_key_up(key)

    def do_on_key_down(self,key):
        pass
    
    def do_on_key_up(self,key):
        pass

    def do_on_get_focus(self)->None:
        pass
        
    def do_on_lose_focus(self)->None:
        pass

    def focus_next_sibling(self)->None:
        if isinstance(self.parent,bf.Container):
            self.parent.focus_next_child()
    def focus_prev_sibling(self)->None:
        if isinstance(self.parent,bf.Container):
            self.parent.focus_prev_child()


    def on_click_down(self,button:int)->None:
        self.is_clicked_down = True
        self.do_on_click_down(button)

    def on_click_up(self,button:int)->None:
        self.is_clicked_down = False
        self.do_on_click_up(button)

    def do_on_click_down(self,button:int)->None:    
        pass

    def do_on_click_up(self,button:int)->None:
        pass

    def on_enter(self)->None:
        self.is_hovered = True
        self.do_on_enter()

    def on_exit(self)->None:
        self.is_hovered = False
        self.is_clicked_down = False
        self.do_on_exit()


    def do_on_enter(self)->None:
        pass

    def do_on_exit(self)->None:
        pass

    def on_mouse_motion(self,x,y)->None:
        pass

    def set_focused_child(self,child:"InteractiveWidget"):
        pass

    def draw_focused(self,camera: bf.Camera)->None:
        pygame.draw.rect(camera.surface,"white",camera.world_to_screen(pygame.FRect(self.rect.x,self.rect.centery-4,8,8)))


    def draw(self, camera: bf.Camera) -> int:
        if not self.visible or not self.surface or not camera.intersects(self.rect):
            return sum([child.draw(camera) for child in self.rect.collideobjectsall(self.children)])
        
        if self.parent and self.clip_to_parent :
            clipped_rect,source_area = self._get_clipped_rect_and_area(camera)
            camera.surface.blit(
                self.surface,
                clipped_rect.topleft,
                source_area,
                special_flags=self.blit_flags
            )
        else:
            camera.surface.blit(
                self.surface, camera.world_to_screen(self.rect),  
                special_flags = self.blit_flags
            )
        if self.focusable and self.is_focused : self.draw_focused(camera)
        return 1 + sum([child.draw(camera) for child in self.rect.collideobjectsall(self.children)])
import batFramework as bf
import pygame
class Panel(bf.Entity):
    def __init__(self, size=None, surface_flags=0) -> None:
        bf.Entity.__init__(self,size=size,surface_flags=surface_flags)
        self.surface = self.surface.convert_alpha()
        self.surface.fill((0,0,0,0))
        self._border_radius = [0]
        self._background_color = None
        self._border_color = None
        self._border_width = None
        self._resizable = True
        self._manual_resized = size!=None
        self._parent_resize_request = None
        self._set_position_center = False

    def set_position(self, x, y):
        self._set_position_center = False
        return super().set_position(x, y)
    
    def set_center(self, x, y):
        self._set_position_center = True
        return super().set_center(x, y)

    def set_resizable(self,value : bool):
        self._resizable = value
        return self

    def resize_by_parent(self,new_width,new_height):
        self._parent_resize_request = (new_width,new_height)
        if not self._manual_resized and self._resizable : 
            if self._set_position_center : tmp = self.rect.center
            if new_width: self.rect.w = new_width 
            if new_height: self.rect.h = new_height
            if self._set_position_center : self.rect.center = tmp
            self.update_surface()

    def resize(self,new_width,new_height,manual_resize = True):
        if self._set_position_center : tmp = self.rect.center
        self.rect.size = (new_width,new_height)
        if self._set_position_center : self.rect.center = tmp
        self._manual_resized = manual_resize
        self.update_surface()
        return self

    def set_border_width(self,width : int):
        self._border_width = width
        self.update_surface()
        return self
    
    def set_border_color(self, color):
        self._border_color = color
        self.update_surface()
        return self
    
    def set_border_radius(self,value:int|list[int]):
        self._border_radius = value if isinstance(value,list) or isinstance(value,tuple) else [value]
        self.update_surface()
        return self

    def set_background_color(self, color):
        self._background_color = color
        self.update_surface()
        return self

    def update_surface(self):
        if self.surface.get_size() != self.rect.size :
            # print(self.uid,self.rect.size)
            self.surface = pygame.Surface(self.rect.size).convert_alpha()
        if not self._background_color:
            self.surface.fill((0,0,0,0))  # Transparent background
        elif any(self._border_radius):
            self.surface.fill((0,0,0,0)) #border_radius background
            pygame.draw.rect(self.surface, self._background_color, (0,0,*self.rect.size), 0, *self._border_radius)
        else: #filled background 
            self.surface.fill(self._background_color)

        if not self._border_width or not self._border_color: return
        pygame.draw.rect(self.surface,self._border_color,(0,0,*self.rect.size),self._border_width,*self._border_radius)

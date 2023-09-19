import batFramework as bf
from .container import Container
import pygame

class TitledContainer(Container):
    def __init__(self,title:str="TITLE", uid=None, layout: bf.Layout = bf.Layout.FILL):
        super().__init__(uid, layout)
        self._title_padding = [2,2]
        self.title_label = bf.Label(title)
        self.set_position(0,0)
    def set_title_padding(self,value):
        self._title_padding = value

    def set_position(self, x, y):
        self.title_label.set_position(x+self._title_padding[0],y+self._title_padding[1])
        return super().set_position(x, self.title_label.rect.bottom+self._title_padding[1])
    
    def set_visible(self, value):
        self.title_label.set_visible(value)
        return super().set_visible(value)


    def get_bounding_box(self):
        yield from super().get_bounding_box()
        yield from self.title_label.get_bounding_box()

    def get_max_child_width(self):
        return max(child.rect.w for child in self.children+[self.title_label]) if self.children else self.rect.w
    def set_center(self,x,y):
        union = self.rect.union(self.title_label.rect.inflate(*self._padding))
        union.center = (x,y)
        super().set_center(*union.center)
        self.title_label.set_position(self.rect.left,self.rect.top-self.title_label.rect.h)
        return self
    
    def draw(self, camera):

        i = super().draw(camera) 
        if i and self._border_width: 
            title_rect = (
                *camera.transpose(self.rect.move(0,-self.title_label.rect.h-self._title_padding[1]*2)).topleft,
                self.rect.w,
                self.title_label.rect.h+self._title_padding[1]*2)
            pygame.draw.rect(camera.surface,self.title_label._background_color,title_rect,0,*self._border_radius)
            pygame.draw.rect(camera.surface,self._border_color,title_rect,self._border_width,*self._border_radius)
        i+=self.title_label.draw(camera)
        return i
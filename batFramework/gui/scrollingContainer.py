import batFramework as bf
from pygame.math import Vector2
from .container import Container
import pygame

class ScrollingContainer(Container):
    def __init__(self, uid=None, layout: bf.Layout = bf.Layout.FILL, size=None):
        self.scroll = Vector2(0,0)
        self.children_rect = pygame.FRect(0,0,0,0)
        super().__init__(uid, layout)
        if size:
            self.resize(*size)
        else:
            self.resize(50, 50)

    def _update_vertical_children(self):
        max_child_width = self.rect.width - self._padding[0]*2

        start_y = self.rect.y + self._padding[1] - self.scroll.y
        self.children_rect = pygame.FRect(0,0,0,0)
        for child in self.children:
            y = start_y
            x = self.rect.left
            if self.layout == bf.Layout.FILL:     
                child.resize_by_parent(max_child_width, None)
            if self.alignment == bf.Alignment.LEFT:
                x = self.rect.x + self._padding[0]
            elif self.alignment == bf.Alignment.RIGHT:
                x = self.rect.right - child.rect.w - self._padding[0]
            elif self.alignment == bf.Alignment.CENTER:
                tmp = child.rect.copy()
                tmp.centerx = self.rect.centerx
                x = tmp.left
            child.set_position(x, y)
            if child.rect.top < self.rect.top + self._padding[1] or child.rect.bottom > self.rect.bottom - self._padding[1]:
                child.set_visible(False)
            else:
                child.set_visible(True)
            start_y = child.rect.bottom + (self.gap if len(self.children) > 1 else 0)
            self.children_rect.union_ip(child.rect)
        

    def get_visible_height(self):
        return (self.rect.h - self._padding[1]*2)
        
    def set_focused_child_index(self,index:int):
        super().set_focused_child_index(index)
        current_child = self.get_focused_child()
        print(current_child._text)
        # self.scroll.y = self.rect.top + current_child.rect.top +self.scroll.y - self._padding[1]
        print(self.children_rect.h,self.get_visible_height(),self.scroll.y,current_child.rect.top)
        # if current_child.rect.bottom > self.rect.top + self.get_visible_height():
            # self.scroll.y = self.rect.top - self.get_visible_height() + self._padding[1] + (current_child.rect.top + self.scroll.y)
        # elif current_child.rect.top <  self.rect.top:
            # self.scroll.y = self.rect.top + self._padding[1] + (current_child.rect.top + self.scroll.y)
        # else:
            # return
        self._update_vertical_children()

    def get_scroll_ratio(self):
        return self.scroll.y *  (self.get_visible_height() / self.children_rect.h)
    def get_scrollbar_height(self):
        return self.get_visible_height() * (self.get_visible_height() / self.children_rect.h)

    # def process_event(self,event):
        # super().process_event(event)
        # if event.type == pygame.MOUSEWHEEL:
            # self.scroll.y += event.y * 30
            # self._update_vertical_children()

    def draw(self,camera):
        i = super().draw(camera)
        scroll_width = 4
        scroll_margin = 2
        scrollbar_rect = pygame.FRect(self.rect.right-scroll_margin-scroll_width,self.rect.top + self.get_scroll_ratio(),scroll_width,self.get_scrollbar_height())
        pygame.draw.rect(camera.surface,bf.color.CLOUD_WHITE,camera.transpose(scrollbar_rect))
        return i

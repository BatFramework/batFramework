import batFramework as bf
from pygame.math import Vector2
from .container import Container
import pygame

class ScrollingContainer(Container):
    def __init__(self, uid=None, layout: bf.Layout = bf.Layout.FILL, size=None):
        self.scroll = Vector2(0,0)
        self.scrollbar_color = bf.color.CLOUD_WHITE
        self.scrollbar_margin = 2
        self.scrollbar_width = 4
        self.scroll_target = pygame.Vector2(0,0)
        self.children_rect = None
        super().__init__(uid, layout)
        if size:
            self.resize(*size)
        else:
            self.resize(50, 50)

    def set_scrollbar_color(self,color):
        self.scrollbar_color = color

    def set_scrollbar_width(self,width):
        self.scrollbar_width = width

    def set_scrollbar_margin(self,margin):
        self.scrollbar_margin = margin


    def _update_vertical_children(self):
        max_child_width = self.rect.width - self._padding[0]*2

        start_y = self.rect.y + self._padding[1] - self.scroll.y
        self.children_rect = None
        for index,child in enumerate(self.children):
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
            if child != self.get_focused_child() and child.rect.top < self.rect.top  or child.rect.bottom > self.rect.bottom :
                child.set_visible(False)
            else:
                child.set_visible(True)
            new_value = child.rect.bottom + (self.gap if index < len(self.children)-1 else 0)
            start_y = new_value
            if self.children_rect is None : 
                self.children_rect = child.rect.copy()
            else:
                self.children_rect.union_ip(child.rect)
        

    def get_visible_height(self):
        return (self.rect.h - self._padding[1]*2)
        
    def set_focused_child_index(self,index:int):
        super().set_focused_child_index(index)
        current_child = self.get_focused_child()

        if index == 0:
            self.set_scroll(0)
        elif current_child.rect.bottom > self.rect.top + self.get_visible_height() -self._padding[1]:
            self.set_scroll(self.rect.top + self._padding[1] + (current_child.rect.top + self.scroll.y) - self.get_visible_height()) 
        elif current_child.rect.top <  self.rect.top + self._padding[1]:
            self.set_scroll(self.rect.top - self._padding[1] + (current_child.rect.top + self.scroll.y))

    def set_scroll(self,value):
        max_scroll = self.rect.top + self.children_rect.h - self.get_visible_height() 
        value = max(min(value,max_scroll),0)
        # self.scroll.y = value
        self.scroll_target.y = value
        # self._update_vertical_children()


    def get_scroll_ratio(self):
        return round(self.scroll.y *  (self.get_visible_height() / self.children_rect.h),1)

    def get_scrollbar_height(self):
        return int(self.get_visible_height() * min(1,(self.get_visible_height() / self.children_rect.h)))

    def process_event(self,event):
        super().process_event(event)
        if event.type == pygame.MOUSEWHEEL:
            if self.rect.collidepoint(*pygame.mouse.get_pos()):

                self.set_scroll(self.scroll.y - event.y * 20)

    def draw(self,camera):
        i = super().draw(camera)
        i+= self.draw_scrollbar(camera)
        return i

    def draw_scrollbar(self,camera:bf.Camera):
        scrollbar_rect = pygame.FRect(self.rect.right-self.scrollbar_margin-self.scrollbar_width,self.rect.top + self._padding[1] + self.get_scroll_ratio(),self.scrollbar_width,self.get_scrollbar_height())
        pygame.draw.rect(camera.surface,self.scrollbar_color,camera.transpose(scrollbar_rect))
        return 1
    
    def update(self, dt):
        super().update(dt)
        if self.scroll_target != self.scroll:
            self.scroll += ((self.scroll_target - self.scroll) * (dt*60)) / 5
            if round(self.scroll.x,1) == round(self.scroll_target.x,1) and\
                round(self.scroll.y,1) == round(self.scroll_target.y,1):
                self.scroll.update(*self.scroll_target)

            self._update_vertical_children()
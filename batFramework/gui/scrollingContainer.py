import batFramework as bf
from pygame.math import Vector2
from .container import Container
import pygame
class ScrollingContainer(Container):
    def __init__(self, uid=None, layout: bf.Layout = bf.Layout.FILL,size=None):
        super().__init__(uid, layout)
        if size : 
            self.resize(*size)
        else:
            self.resize(50,50) 
        self.scroll = Vector2()


    def get_offset_position(self,x,y):
        return -self.scroll + (x,y)

    def next(self):

        self.interactive_children[self.focused_index].lose_focus()
        new_index  = min((self.focused_index + 1) , len(self.interactive_children)-1)
        if new_index != self.focused_index :         
            self.focused_index = new_index 
            self.interactive_children[self.focused_index].get_focus()
            if self.switch_focus_sfx  : bf.AudioManager().play_sound(self.switch_focus_sfx ,self._sfx_volume)
            self.scroll.y += self.get_focused_child().rect.h + self.gap
        # print(self.focused_index)

    def prev(self):
        self.interactive_children[self.focused_index].lose_focus()
        new_index = max((self.focused_index - 1),0)
        if new_index != self.focused_index:
            self.focused_index = new_index
            self.interactive_children[self.focused_index].get_focus()
            if self.switch_focus_sfx  : bf.AudioManager().play_sound(self.switch_focus_sfx ,self._sfx_volume)
            self.scroll.y -= self.get_focused_child().rect.h - self.gap
        # print(self.focused_index)



    def draw_focused_child(self, camera):
        child = self.get_focused_child()
        super().draw_focused_child(camera)
        pygame.draw.rect(camera.surface,bf.color.ORANGE,(*child.rect.topleft,3,3))


    def get_indicator_ratio(self):
        len_children = len(self.children)
        total_children_height = sum(child.rect.h for child in self.children)
        total_gap_height = max(0,(len_children - 1) * self.gap)
        total_height = max(0,total_children_height + total_gap_height + self._padding[1]*2)

        return self.rect.h / total_height
    def draw(self, camera:bf.Camera):
        """
        Draw the container and its children.

        Parameters:
            camera (Camera): The camera to draw the container onto.

        Returns:
            int: The number of entities drawn.
        """
        if not self.visible:
            return 0
        num_drawn = 1
        camera.surface.blit(self.surface,camera.transpose(self.rect))
        for child in [c for c in self.children if c.rect.move(*-self.scroll).colliderect(self.rect.inflate(-self._padding[0]*2,-self._padding[1]*2))  and c.visible  and not ( isinstance(c, bf.InteractiveEntity) and  c._focused)]:
            child.draw(camera)
            num_drawn += 1
        if self._focused and self.get_focused_child().rect.move(*-self.scroll).colliderect(self.rect.inflate(-self._padding[0]*2,-self._padding[1]*2)) :
            self.draw_focused_child(camera)
            num_drawn +=1
        pygame.draw.rect(
            camera.surface,
            bf.color.CLOUD_WHITE,
            (*camera.transpose(self.rect).move(-4,self._padding[1] + int(self.scroll.y * self.get_indicator_ratio())).topright,2,int(self.rect.h * self.get_indicator_ratio() )))

        return num_drawn

import batFramework as bf
from .frame import Frame


class TitledFrame(Frame):
    def __init__(
        self,
        title="",
        text_size=None,
        alignment: bf.Alignment = bf.Alignment.CENTER,
        size=None,
    ):
        super().__init__(size)
        self._title_padding = [2,2]
        self.title_label = bf.Label(title)
        self.title_label.resize_by_parent(self.rect.w- 2*self._title_padding[0],None)
        self.set_position(0,0)

    def set_title_padding(self,value):
        self._title_padding = value


    def resize(self, new_width, new_height, manual_resize=True):
        super().resize(new_width, new_height, manual_resize)
        self.title_label.resize_by_parent(self.rect.w- 2*self._title_padding[0],None)
        return self
    
    def set_position(self, x, y):
        self.title_label.set_position(x+self._title_padding[0],y+self._title_padding[1])
        return super().set_position(x,y)
    
    def get_bounding_box(self):
        return self.rect, *self.title_label.get_bounding_box()
    
    def set_visible(self, value):
        self.title_label.set_visible(value)
        return super().set_visible(value)


    def get_bounding_box(self):
        yield from super().get_bounding_box()
        yield from self.title_label.get_bounding_box()

    def set_center(self,x,y):
        union = self.rect.union(self.title_label.rect)
        union.center = (x,y)
        super().set_center(*union.center)
        self.title_label.set_position(self.rect.left,self.rect.top-self.title_label.rect.h)
        return self
    
    def set_border_radius(self, value: int | list[int]):
        super().set_border_radius(value)
        self.title_label.set_border_radius(value)
        return self

    def update_surface(self):
        super().update_surface()
        self.title_label.update_surface()

    def draw(self, camera: bf.Camera) -> bool:
        i = super().draw(camera)
        i += self.title_label.draw(camera)
        return i

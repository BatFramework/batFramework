import batFramework as bf
from .panel import Panel


class TitledFrame(Panel):
    def __init__(
        self,
        text="",
        text_size=None,
        alignment: bf.Alignment = bf.Alignment.CENTER,
        size=None,
    ):
        super().__init__(size)
        self.title_label = bf.Label(text, text_size)
        self.title_label.set_position(*self.rect.topleft)
        # self.set_size(*self.rect.size)

    def get_bounding_box(self):
        return self.rect, *self.title_label.get_bounding_box()

    def set_position(self, x, y):
        super().set_position(x, y)
        self.title_label.set_position(x, y)
        return self

    def set_center(self, x, y):
        super().set_center(x, y)
        self.title_label.set_position(*self.rect.topleft)
        return self

    def set_border_radius(self, value: int | list[int]):
        super().set_border_radius(value)
        self.title_label.set_border_radius(value)
        return self

    def update_surface(self):
        super().update_surface()
        self.title_label.update_surface()

    def draw(self, camera: bf.Camera) -> bool:
        i = 0
        i += super().draw(camera)
        i += self.title_label.draw(camera)
        return i

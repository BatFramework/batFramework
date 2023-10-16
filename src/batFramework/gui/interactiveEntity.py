import batFramework as bf


class InteractiveEntity(bf.Entity):
    def __init__(self) -> None:
        super().__init__()
        self._focused = False

    def get_focus(self):
        if self.parent_container and not self._focused:
            # self.parent_container.focused_index = self.parent_container.interactive_children.index(self)
            self.parent_container.set_focused_child(self)
        self._focused = True

    def lose_focus(self):
        self._focused = False

    def has_focus(self):
        return self._focused

    def draw_focused(self, camera: bf.Camera):
        return self.draw(camera)

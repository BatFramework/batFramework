from .baseScene import BaseScene
import batFramework as bf


class Scene(BaseScene):
    def __init__(self,name: str) -> None:
        """
        Default Scene object.
        Has 2 layers (world and hud) by default
        Contains an exposed root gui object on the hud layer
        Args:
            name: Name of the scene.
        """
        super().__init__(name)
        self.add_layer(bf.SceneLayer("world",True))
        hud_layer = bf.SceneLayer("hud",True)
        self.add_layer(hud_layer)
        self.root: bf.gui.Root = bf.gui.Root(hud_layer.camera)
        self.root.rect.center = hud_layer.camera.get_center()
        self.add("hud",self.root)
        self.entities_to_remove = []
        self.entities_to_add = []

    def on_enter(self):
        self.root.clear_hovered()
        self.root.build()
        super().on_enter()

    def on_exit(self):
        self.root.clear_hovered()
        super().on_exit()

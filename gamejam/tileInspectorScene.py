from custom_scenes import CustomBaseScene



class TileInspectorScene(CustomBaseScene):
    def __init__(self) -> None:
        super().__init__("tile_inspector",False)
        self.inspected_tile = None


    def do_when_added(self):
        self.manager.set_sharedVar("inspected_tile",None)
    

    def on_enter(self):
        pass
import batFramework as bf


class CutsceneBlock:
    ...


class Cutscene:
    ...


class CutsceneManager(metaclass=bf.Singleton):
    def __init__(self, manager) -> None:
        self.current_cutscene: Cutscene = None
        self.cutscenes: list[bf.Cutscene] = []
        self.manager: bf.Manager = manager

    def get_flag(self, flag):
        return None

    def process_event(self, event):
        if self.current_cutscene:
            self.current_cutscene.process_event(event)

    def queue(self, *cutscenes):
        self.cutscenes.extend(cutscenes)
        if self.current_cutscene is None:
            self.play(self.cutscenes.pop(0))

    def play(self, cutscene: Cutscene):
        if self.current_cutscene is None:
            self.current_cutscene = cutscene
            self.current_cutscene.on_enter()
            self.current_cutscene.init_blocks()
            self.current_cutscene.play()
        self.manager.set_sharedVar("in_cutscene", True)

    def update(self, dt):
        if not self.current_cutscene is None:
            self.current_cutscene.update(dt)
            # print("cutscene manager update")
            if self.current_cutscene.has_ended():
                self.current_cutscene.on_exit()
                self.current_cutscene = None
                if self.cutscenes:
                    self.play(self.cutscenes.pop(0))
                else:
                    self.current_cutscene = None
                    self.manager.set_sharedVar("in_cutscene", False)


class Cutscene:
    def __init__(self, *blocks) -> None:
        self.cutscene_blocks: list[CutsceneBlock] = list(blocks)
        self.block_index = 0
        self.end_blocks: list[CutsceneBlock] = []
        self.ended = False

    def on_enter(self):
        pass

    def on_exit(self):
        pass

    def init_blocks(self):
        pass

    def add_end_block(self, block):
        block.set_parent_cutscene(self)
        self.end_blocks.append(block)

    def get_scene_at(self, index):
        return bf.CutsceneManager().manager._scenes[index]

    def get_current_scene(self):
        return bf.CutsceneManager().manager.get_current_scene()

    def set_scene(self, name, index=0):
        return bf.CutsceneManager().manager.set_scene(name, index)

    def get_scene(self, name):
        return bf.CutsceneManager().manager.get_scene(name)

    def add_block(self, *blocks: list[CutsceneBlock]):
        for block in blocks:
            block.set_parent_cutscene(self)
            self.cutscene_blocks.append(block)

    def process_event(self, event):
        if not self.ended and self.block_index < len(self.cutscene_blocks):
            self.cutscene_blocks[self.block_index].process_event(event)

    def play(self):
        self.block_index = 0
        if self.cutscene_blocks:
            self.cutscene_blocks[self.block_index].start()
        else:
            self.ended

    def update(self, dt):
        if self.ended:
            return
        # print("cutscene update",self.cutscene_blocks[self.block_index])
        self.cutscene_blocks[self.block_index].update(dt)
        if self.cutscene_blocks[self.block_index].has_ended():
            self.block_index += 1
            if self.block_index == len(self.cutscene_blocks):
                if not self.end_blocks:
                    self.ended = True
                    return
                else:
                    self.cutscene_blocks.extend(self.end_blocks)
                    self.end_blocks = []
            self.cutscene_blocks[self.block_index].start()

            # print("NEXT BLOCK")

    def has_ended(self):
        return self.ended

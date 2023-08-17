import batFramework as bf


class CutsceneBlock:
    ...


class Cutscene:
    ...


class CutsceneManager(metaclass=bf.Singleton):
    def __init__(self, manager) -> None:
        self.current_cutscene: Cutscene = None
        self.manager: bf.Manager = manager

    def get_flag(self, flag):
        return None

    def process_event(self, event):
        if self.current_cutscene:
            self.current_cutscene.process_event(event)

    def play(self, cutscene: Cutscene):
        if self.current_cutscene is None:
            self.current_cutscene = cutscene
            self.current_cutscene.play()
        self.manager.set_sharedVar("in_cutscene", True)

    def update(self, dt):
        if not self.current_cutscene is None:
            self.current_cutscene.update(dt)
            # print("cutscene manager update")
            if self.current_cutscene.has_ended():
                self.current_cutscene.on_exit()
                self.manager.set_sharedVar("in_cutscene", False)
                self.current_cutscene = None

class Cutscene:
    def __init__(self) -> None:
        self.cutscene_blocks: list[CutsceneBlock] = []
        self.block_index = 0
        self.ended = False

    def on_exit(self):
        pass

    def get_current_scene(self):
        return bf.CutsceneManager().manager.get_current_scene()
    
    def get_scene(self,name):
        return bf.CutsceneManager().manager.get_scene(name)
    
    def add_block(self, *blocks: list[CutsceneBlock]):
        for block in blocks:
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
                self.ended = True
                return
            self.cutscene_blocks[self.block_index].start()

            # print("NEXT BLOCK")

    def has_ended(self):
        return self.ended


# Define the base CutsceneBlock class
class CutsceneBlock:
    """
    Base class for cutscene blocks. Represents a unit of action in a cutscene.
    """

    # Constructor for the CutsceneBlock
    def __init__(self) -> None:
        # Callback function, parent cutscene, and state variables
        self.callback = None
        self.parent_cutscene: Cutscene = None
        self.get_flag = CutsceneManager().get_flag
        self.ended = False
        self.started = False


    def get_current_scene(self):
        return bf.CutsceneManager().manager.get_current_scene()
    
    def get_scene(self,name):
        return bf.CutsceneManager().manager.get_scene(name)
    
    # Set the parent cutscene for this block
    def set_parent_cutscene(self, parent):
        """
        Set the parent cutscene for this block.

        Args:
            parent: The parent cutscene object.
        """
        self.parent_cutscene = parent

    # Process an event (placeholder implementation, to be overridden in subclasses)
    def process_event(self, event):
        """
        Process an event for this cutscene block.

        Args:
            event: The event to be processed.
        """
        pass

    # Update the block (placeholder implementation, to be overridden in subclasses)
    def update(self, dt):
        """
        Update the cutscene block.

        Args:
            dt: Time elapsed since the last update.
        """
        pass

    # Start the block
    def start(self):
        """
        Start the cutscene block.
        """
        self.started = True

    # Mark the block as ended
    def end(self):
        """
        Mark the cutscene block as ended.
        """
        self.ended = True

    # Check if the block has ended
    def has_ended(self):
        """
        Check if the cutscene block has ended.

        Returns:
            bool: True if the block has ended, False otherwise.
        """
        return self.ended

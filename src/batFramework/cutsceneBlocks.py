import batFramework as bf
from .cutscene import Cutscene, CutsceneManager


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

    def get_scene_at(self, index):
        return bf.CutsceneManager().manager._scenes[index]

    def set_scene(self, name, index=0):
        return CutsceneManager().manager.set_scene(name, index)

    def get_current_scene(self):
        return CutsceneManager().manager.get_current_scene()

    def get_scene(self, name):
        return CutsceneManager().manager.get_scene(name)

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


# Define the ParallelBlock class, a type of CutsceneBlock
class ParallelBlock(CutsceneBlock):
    """
    Represents a parallel execution block for multiple Cutscene blocks.
    """

    # Constructor for ParallelBlock, taking a variable number of blocks as arguments
    def __init__(self, *blocks) -> None:
        super().__init__()
        # List of blocks to run in parallel
        self.blocks: list[CutsceneBlock] = blocks

    # Start the parallel block (override the base class method)
    def start(self):
        """
        Start the parallel execution block.
        """
        super().start()
        # Start each block in parallel
        for block in self.blocks:
            block.start()

    # Process an event for each block in parallel
    def process_event(self, event):
        """
        Process an event for each block in the parallel execution block.

        Args:
            event: The event to be processed.
        """
        _ = [b.process_event(event) for b in self.blocks]

    # Update each block in parallel
    def update(self, dt):
        """
        Update each block in the parallel execution block.

        Args:
            dt: Time elapsed since the last update.
        """
        _ = [b.update(dt) for b in self.blocks]

    # Check if all blocks have ended
    def has_ended(self):
        """
        Check if all blocks in the parallel execution block have ended.

        Returns:
            bool: True if all blocks have ended, False otherwise.
        """
        return all(b.has_ended() for b in self.blocks)


# Define the SceneTransitionBlock class, a type of CutsceneBlock
class SceneTransitionBlock(CutsceneBlock):
    """
    Represents a scene transition Cutscene block.
    """

    # Constructor for SceneTransitionBlock
    def __init__(self, scene, transition, duration, **kwargs) -> None:
        super().__init__()
        # Target scene, transition type, duration, and additional keyword arguments
        self.target_scene = scene
        self.transition = transition
        self.duration = duration
        self.kwargs = kwargs
        # Timer to handle the end of the transition
        self.timer = bf.Timer(
            name="scene_transition_block", duration=duration, end_callback=self.end
        )

    # Start the scene transition block
    def start(self):
        """
        Start the scene transition block.
        """
        super().start()
        print(f"transition to {scene}")

        # Initiate the scene transition
        if self.get_current_scene()._name == self.target_scene:
            self.end()
            return
        CutsceneManager().manager.transition_to_scene(
            self.target_scene, self.transition, duration=self.duration, **self.kwargs
        )
        # Start the timer to handle the end of the transition
        self.timer.start()

    def end(self):
        return super().end()

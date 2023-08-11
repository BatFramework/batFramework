import batFramework as bf


# Define the ParallelBlock class, a type of bf.CutsceneBlock
class ParallelBlock(bf.CutsceneBlock):
    """
    Represents a parallel execution block for multiple bf.Cutscene blocks.
    """

    # Constructor for ParallelBlock, taking a variable number of blocks as arguments
    def __init__(self, *blocks) -> None:
        super().__init__()
        # List of blocks to run in parallel
        self.blocks: list[bf.CutsceneBlock] = blocks

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


# Define the SceneTransitionBlock class, a type of bf.CutsceneBlock
class SceneTransitionBlock(bf.CutsceneBlock):
    """
    Represents a scene transition bf.Cutscene block.
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
        self.timer = bf.Time().timer(duration=duration, callback=self.end)

    # Start the scene transition block
    def start(self):
        """
        Start the scene transition block.
        """
        super().start()
        # Initiate the scene transition
        bf.CutsceneManager().manager.transition_to_scene(
            self.target_scene, self.transition, self.duration, **self.kwargs
        )
        # Start the timer to handle the end of the transition
        self.timer.start()
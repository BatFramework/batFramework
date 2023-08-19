import batFramework as bf


class DialogueBlock(bf.CutsceneBlock):
    def __init__(
        self, message, character=None, emotion=None, delay=1000, facing_right=None,
        scene=None
    ) -> None:
        super().__init__()
        self.message = message
        self.char = character
        self.emotion = emotion
        self.facing_right = facing_right
        self.scene = scene

        self.timer = bf.Timer(
            duration=delay,
            end_callback=self.timer_callback
        )
    def timer_callback(self):
        self.get_scene("dialogue").say(self.message, callback=self.end)

    def start(self):
        super().start()
        # bf.CutsceneManager().manager.set_scene("dialogue")
        # print("dialog set sprite : ",self.char, self.emotion, self.facing_right)
        self.timer.start()


class SetSpriteBlock(bf.CutsceneBlock):
    def __init__(self, character=None, emotion=None, facing_right=None,scene=None) -> None:
        super().__init__()
        self.char = character
        self.emotion = emotion
        self.facing_right = facing_right
        self.scene = scene
    def start(self):
        super().start()
        # print("set sprite block")
        # if self.scene is None:
        #     self.get_scene("dialogue").set_sprite(
        #     self.char, self.emotion, self.facing_right
        # )
        self.end()


class ImageBlock(bf.CutsceneBlock):
    def __init__(self, image_path, duration=1, hide_at_exit=False,scene=None) -> None:
        super().__init__()
        self.image_path = image_path
        self.hide_at_exit = hide_at_exit
        self.scene = scene
        self.timer = bf.Timer(duration=duration, end_callback=self.end)

    def start(self):
        super().start()

        self.timer.start()

    def end(self):
        # if self.hide_at_exit:

        return super().end()


class DelayBlock(bf.CutsceneBlock):
    def __init__(self, duration) -> None:
        super().__init__()
        self.timer = bf.Timer(duration=duration, end_callback=self.end)

    def start(self):
        super().start()
        self.timer.start()

class DialogueFadeIn(bf.CutsceneBlock):
    def __init__(self,duration) -> None:
        super().__init__()
        self.duration = duration
    def start(self):
        super().start()
        self.get_scene("dialogue").fade_in(self.duration)
        bf.Timer(duration=self.duration,end_callback=self.end).start()


class DialogueFadeOut(bf.CutsceneBlock):
    def __init__(self,duration) -> None:
        super().__init__()
        self.duration = duration
    def start(self):
        super().start()
        self.get_scene("dialogue").fade_out(self.duration)
        bf.Timer(duration=self.duration,end_callback=self.end).start()
    
    def end(self):
        self.set_scene(bf.CutsceneManager().manager._scenes[1]._name)
        return super().end()


class BgSceneTransitionBlock(bf.SceneTransitionBlock):
    # Start the scene transition block
    def start(self):
        bf.CutsceneBlock.start(self)
        # Initiate the scene transition
        if self.get_current_scene()._name == self.target_scene:
            self.end()
            return
        bf.CutsceneManager().manager.transition_to_scene(
            self.target_scene, self.transition, duration=self.duration,index=1, **self.kwargs
        )
        # Start the timer to handle the end of the transition
        self.timer.start()


class MoveCamera(bf.CutsceneBlock):
    def __init__(self) -> None:
        super().__init__()
            




class CustomCutsceneBase(bf.Cutscene):
    def on_enter(self):
        self.set_scene("dialogue")
        self.add_block(DialogueFadeIn(300))

    def on_exit(self):
        bf.CutsceneManager().queue(bf.Cutscene(DialogueFadeOut(300)))




class IntroCutscene(CustomCutsceneBase):
    def init_blocks(self) -> None:
        self.add_block(
            # DelayBlock(500),
            DialogueBlock("TEXT HERE"),
            BgSceneTransitionBlock("game",bf.FadeTransition,duration=1000),
            DelayBlock(500),
        )


class EditorTutorial(CustomCutsceneBase):
    def init_blocks(self):
        self.add_block(
            # SetSpriteBlock("baby","happy"),
            DelayBlock(500),
            DialogueBlock("This is the editor screen !\nPress the 'q' key to enter the tile picker !","baby","happy"),
            DelayBlock(500),
        )


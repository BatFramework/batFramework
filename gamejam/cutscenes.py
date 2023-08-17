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
        if self.scene is None:
            self.get_current_scene().say(self.message, callback=self.end)
        else:
            self.get_scene(self.scene).say(self.message, callback=self.end)

    def start(self):
        super().start()
        # print("dialog set sprite : ",self.char, self.emotion, self.facing_right)
        if any(val is not None for val in [self.char,self.emotion,self.facing_right]):
            if self.scene is None:
                self.get_current_scene().set_sprite(
                self.char, self.emotion, self.facing_right
            )
            else:
                self.get_scene(self.scene).set_sprite(
                self.char, self.emotion, self.facing_right
            )
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
        if self.scene is None:
            self.get_current_scene().set_sprite(
            self.char, self.emotion, self.facing_right
        )
        else:
            self.get_scene(self.scene).set_sprite(
            self.char, self.emotion, self.facing_right
        )
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
        if self.scene is None:
            self.get_current_scene().set_background(self.image_path)
        else:
            self.get_scene(self.scene).set_background(self.image_path)
        self.timer.start()

    def end(self):
        if self.hide_at_exit:
            if self.scene is None:
                self.get_current_scene().set_background(None)
            else:
                self.get_scene(self.scene).set_background(None)
        return super().end()


class DelayBlock(bf.CutsceneBlock):
    def __init__(self, duration) -> None:
        super().__init__()
        self.timer = bf.Timer(duration=duration, end_callback=self.end)

    def start(self):
        super().start()
        self.timer.start()

class CustomCutsceneBase(bf.Cutscene):
    def on_exit(self):
        # print("custom exit")
        current_scene  = self.get_current_scene()
        current_scene.set_background(None)
        current_scene.set_sprite()
                


class IntroCutscene(CustomCutsceneBase):
    def __init__(self) -> None:
        super().__init__()
        self.add_block(
            bf.SceneTransitionBlock(
                scene="game", transition=bf.FadeTransition, duration=300
            ),
            # DelayBlock(1000),
            SetSpriteBlock("baby","happy",scene="game"),
            # ImageBlock(image_path="backgrounds/sky.png"),

            DialogueBlock("Did you see that cool fading effect ?"),
            SetSpriteBlock("player","thinking",facing_right=False),
            DelayBlock(1000),
            DialogueBlock("Meh..","player","neutral"),
            DialogueBlock("Alright then check this out : Try pressing the 'e' key on your keyboard !","baby","happy"),
            DelayBlock(1000)

        )


class EditorTutorial(CustomCutsceneBase):
    def __init__(self) -> None:
        super().__init__()
        self.add_block(
            # SetSpriteBlock("baby","happy"),
            DelayBlock(500),
            DialogueBlock("This is the editor screen !\nPress the 'q' key to enter the tile picker !","baby","happy"),
            DelayBlock(500),
        )


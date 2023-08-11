import batFramework as bf

class DialogueBlock(bf.CutsceneBlock):
    def __init__(self,message,character=None,emotion=None,delay=1000,facing_right=True) -> None:
        super().__init__()
        self.message = message
        self.char = character
        self.emotion = emotion
        self.facing_right = facing_right
        self.timer = bf.Time().timer(duration=delay,callback=lambda : bf.CutsceneManager().manager.get_scene("dialogue").say(self.message,callback = self.end))

    def start(self):
        super().start()
        bf.CutsceneManager().manager.get_scene("dialogue").set_sprite(self.char,self.emotion,self.facing_right)
        self.timer.start()

class SetSpriteBlock(bf.CutsceneBlock):
    def __init__(self,character=None,emotion=None,facing_right = True) -> None:
        super().__init__()
        self.char = character
        self.emotion = emotion
        self.facing_right = facing_right

    def start(self):
        super().start()
        bf.CutsceneManager().manager.get_scene("dialogue").set_sprite(self.char,self.emotion,self.facing_right)
        self.ended = True

class ImageBlock(bf.CutsceneBlock):
    def __init__(self,image_path,duration=None,hide_at_exit=False) -> None:
        super().__init__()
        # self.image = bf.Image(image_path)
        if duration is None : duration = 0
        self.image_path = image_path
        self.hide_at_exit = hide_at_exit
        self.timer = bf.Time().timer(duration=duration,callback=self.end)

    def start(self):
        super().start()
        bf.CutsceneManager().manager.get_scene("dialogue").set_background(self.image_path)
        self.timer.start()

    def end(self):
        if self.hide_at_exit : bf.CutsceneManager().manager.get_scene("dialogue").set_background(None)
        return super().end()



class DelayBlock(bf.CutsceneBlock):
    def __init__(self,duration) -> None:
        super().__init__()
        self.timer = bf.Time().timer(duration=duration,callback=self.end)
    
    def start(self):
        super().start()
        self.timer.start()


class IntroCutscene(bf.Cutscene):


    def __init__(self) -> None:
        super().__init__()
        self.add_block(
            ImageBlock(image_path="backgrounds/sky.png"),

            SetSpriteBlock("player"),

            bf.SceneTransitionBlock(scene="dialogue",transition=bf.FadeColorTransition,duration=300,color=bf.color.DARK_GB),

            DialogueBlock(
                "So\nhere's the thing.",
                "player"
            ),
            DialogueBlock("I didn't have enough time to make the story or good levels...","player","thinking"),

            DialogueBlock("So you can make your own :)","player","neutral"),

            DelayBlock(1000),

            DialogueBlock("Press the 'e' key to switch to edit mode !","baby","happy"),

            DelayBlock(1000),

            SetSpriteBlock("baby","neutral",facing_right=False),

            DelayBlock(1000),

            SetSpriteBlock("baby","neutral"),

            DialogueBlock(
                "And you can use the tile picker with the 'q' key, or so I'm told.",
                "baby","happy"
            ),
            DelayBlock(1000),
            
            bf.SceneTransitionBlock(scene="game",transition=bf.FadeTransition,duration=300)
        )
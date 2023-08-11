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
            bf.ParallelBlock(
                DialogueBlock("""The moonlight painted patterns on the forest floor, as if the stars themselves had come down to dance among the trees. \
A gentle breeze whispered secrets through the leaves, and the night held its breath in anticipation of the wonders that lay ahead. \
In this tranquil moment, the world seemed to pause, and every rustle of a leaf felt like a symphony, every flicker of a firefly like a beacon of magic. \
As the river meandered through the valley, it carried with it the stories of generations, the laughter of children, and the dreams of those \
who had looked upon its waters. The mountains stood as ancient sentinels, their majestic peaks kissed by the first light of dawn. \
The sky, a canvas of infinite possibilities, painted with hues of orange and pink, promised a day filled with adventure and discovery. \
In the heart of this wilderness, a lone cabin stood, its windows glowing with the warm light of a hearth.\
Inside, the aroma of freshly baked bread mingled with the earthy scent of pine, creating a haven of comfort and nostalgia.\
A worn book sat on the table, its pages filled with tales of distant lands and daring heroes, waiting to transport the reader to places only imaginable.\
Outside, a canopy of stars emerged, each one telling a story of its own, connecting the past with the present, and hinting at the mysteries of the cosmos.\
In this haven of tranquility, time seemed to lose its grip, allowing the soul to wander freely, to explore the beauty of the world and the depths of the human spirit.""",
                "player"
                ),bf.SceneTransitionBlock(scene="game",transition=bf.FadeTransition,duration=300),

            bf.SceneTransitionBlock(scene="dialogue",transition=bf.FadeColorTransition,duration=300,color=bf.color.ORANGE)

            )
        )

        # self.add_block(
        #     ImageBlock(image_path="backgrounds/sky.png"),
        #     SetSpriteBlock("player"),
        #     bf.SceneTransitionBlock(scene="dialogue",transition=bf.FadeColorTransition,duration=300,color=bf.color.DARK_GB),
        #     # DelayBlock(1000),
        #     DialogueBlock(
        #         "So\nhere's the thing.",
        #         "player"
        #     ),
        #     DialogueBlock(
        #         "So\nhere's the thing.",
        #         "player"
        #     ),
        #     DialogueBlock("I didn't have enough time to make the story or good levels...","player","thinking"),
        #     DialogueBlock("So you can make your own :)","player","neutral"),
        #     DelayBlock(1000),
        #     DialogueBlock("Press the 'e' key to switch to edit mode !","baby","happy"),
        #     DelayBlock(1000),
        #     SetSpriteBlock("baby","neutral",facing_right=False),
        #     DelayBlock(1000),
        #     SetSpriteBlock("baby","neutral"),
        #     DialogueBlock(
        #         "And you can use the tile picker with the 'q' key, or so I'm told.",
        #         "baby","happy"
        #     ),
        #     DelayBlock(1000),
        #     bf.SceneTransitionBlock(scene="game",transition=bf.FadeTransition,duration=300)
        #     )
import batFramework as bf
import pygame
from pygame.math import Vector2

    
class Say(bf.CutsceneBlock):
    def __init__(
        self, message, character="", emotion="", delay=1000, facing_right=None,
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
        self.get_scene("dialogue").set_character(self.char,self.emotion,self.facing_right)
        self.timer.start()


class SetCharacter(bf.CutsceneBlock):
    def __init__(self, character="", emotion="", facing_right=None,scene=None) -> None:
        super().__init__()
        self.char = character
        self.emotion = emotion
        self.facing_right = facing_right
        self.scene = scene
    def start(self):
        super().start()
        print("set sprite block")
        self.get_scene("dialogue").set_character(
            self.char, self.emotion, self.facing_right
        )
        self.end()


class Image(bf.CutsceneBlock):
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


class Wait(bf.CutsceneBlock):
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
    def __init__(self,duration,switch_scenes:bool=True) -> None:
        super().__init__()
        self.duration = duration
        self.switch_scenes =switch_scenes
    def start(self):
        super().start()
        self.get_scene("dialogue").fade_out(self.duration)
        bf.Timer(duration=self.duration,end_callback=self.end).start()
    
    def end(self):
        if self.switch_scenes : 
            self.set_scene(bf.CutsceneManager().manager._scenes[1]._name)
        return super().end()


class BgSceneTransition(bf.SceneTransitionBlock):
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



class ExecuteFunction(bf.CutsceneBlock):
    def __init__(self,func):
        super().__init__()
        self.func = func
    def start(self):
        super().start()
        self.func()
        self.end()

class MoveTo(bf.CutsceneBlock):
    def __init__(self,x,y,duration=1,scene_index=1,end_wait=0) -> None:
        super().__init__()
        self.scene_index = scene_index
        self.origin = Vector2()
        self.destination = Vector2(x,y)
        self.duration = duration
        self.scene_index = scene_index
        self.end_wait = end_wait


    def start(self):
        super().start()
        follow_function = self.get_scene_at(1).camera.follow_point_func
        self.get_scene_at(1).camera.set_follow_dynamic_point(None)
        if follow_function is not None :
            self.parent_cutscene.add_end_block(
                ExecuteFunction(
                    lambda : self.get_scene_at(1).camera.set_follow_dynamic_point(follow_function))
            )

        self.origin.update(*self.get_scene_at(self.scene_index).camera.get_center())
        bf.EasingAnimation(
            duration=self.duration,easing_function=bf.Easing.EASE_IN_OUT,
            update_callback=self.update_callback
        ).start()
        self.end_timer = bf.Timer(duration = self.duration + self.end_wait,end_callback = self.end).start()

    def update_callback(self,progression):
        self.get_scene_at(self.scene_index).camera.set_center(*self.origin.lerp(self.destination,progression))

class MoveBy(bf.CutsceneBlock):
    def __init__(self,x,y,duration=1,scene_index=1,end_wait=0) -> None:
        super().__init__()
        self.scene_index = scene_index
        self.origin = Vector2()
        self.destination = Vector2()
        self.delta = (x,y)
        self.duration = duration
        self.scene_index = scene_index
        self.end_wait = end_wait

    def start(self):
        super().start()
        follow_function = self.get_scene_at(1).camera.follow_point_func
        self.get_scene_at(1).camera.set_follow_dynamic_point(None)
        if follow_function is not None :
            self.parent_cutscene.add_end_block(
                ExecuteFunction(
                    lambda : self.get_scene_at(1).camera.set_follow_dynamic_point(follow_function))
            )
        self.origin.update(*self.get_scene_at(self.scene_index).camera.get_center())
        self.destination.update(*self.origin + Vector2(self.delta))
        bf.EasingAnimation(
            duration=self.duration,easing_function=bf.Easing.EASE_IN_OUT,
            update_callback=self.update_callback
        ).start()
        self.end_timer = bf.Timer(duration = self.duration + self.end_wait,end_callback = self.end).start()
    def update_callback(self,progression):
        self.get_scene_at(self.scene_index).camera.set_center(*self.origin.lerp(self.destination,progression))


class Zoom(bf.CutsceneBlock):
    def __init__(self,target_zoom:float,duration:int,scene_index =1):
        super().__init__()
        self.target_zoom = Vector2(target_zoom,0)
        self.duration = duration
        self.scene_index = scene_index
        self.start_zoom = 1
    def start(self):
        super().start()
        self.start_zoom = Vector2(self.get_scene_at(self.scene_index).camera.zoom_factor,0)

        bf.EasingAnimation(
            duration=self.duration,
            easing_function=bf.Easing.EASE_IN_OUT_ELASTIC,
            update_callback=self.zoom_update,
            end_callback=self.end).start()
    def zoom_update(self,progression):
        delta = self.target_zoom.x - self.start_zoom.x
        zoom_value = delta * progression
        # print(progression,delta,self.start_zoom.x + zoom_value)
        self.get_scene_at(self.scene_index).camera.zoom(self.start_zoom.x + zoom_value)

class CustomCutsceneBase(bf.Cutscene):
    def on_enter(self):
        self.set_scene("dialogue")
        # self.add_block(DialogueFadeIn(300))

    def on_exit(self):
        bf.CutsceneManager().queue(bf.Cutscene(DialogueFadeOut(300)))




class IntroCutscene(CustomCutsceneBase):
    def init_blocks(self) -> None:
        self.add_block(
            SetCharacter(character="player",emotion="neutral"),
            DialogueFadeIn(300),
            Say(message="Okay so...", delay=600),
            SetCharacter(emotion="thinking"),
            Wait(1500),
            Say("I basically rewrote all the code to display dialogues...", emotion="neutral"),
            Say("I'm kinda tired so let's get this over with. I'll start with showing you around..."),
            DialogueFadeOut(300,switch_scenes=False),
            Wait(300),
            BgSceneTransition("game", bf.FadeColorTransition, duration=1000,color=bf.color.DARK_GB),
            Wait(1000),
            Zoom(2,800),
            Wait(1000),
            DialogueFadeIn(300),
            Say("This is me and that little kid..."),
            Say("Guess we look kinda weird from here huh ?",emotion="thinking"),
            DialogueFadeOut(300,False),
            Zoom(1,800),
            Wait(1000),
            BgSceneTransition("tile_picker", bf.FadeColorTransition, duration=1000,color=bf.color.DARK_GB),
            Wait(1000),
            BgSceneTransition("editor", bf.FadeColorTransition, duration=1000,color=bf.color.DARK_GB),
            Wait(1000),
            BgSceneTransition("game", bf.FadeColorTransition, duration=1000,color=bf.color.DARK_GB),
            Wait(1000),
            SetCharacter("player","thinking"),
            DialogueFadeIn(1000),
            Say("I gotta say that was pretty cool...",delay=300),
            Say("I know right :)","baby","happy",delay=300,facing_right=False),
            Say("Yeah anyway let's get back to business. I think we should head this way...","player"),
            DialogueFadeOut(300,False),
            MoveBy(100, 0, duration=1000, end_wait=1000),
            Wait(500),
            MoveBy(-100, 0, duration=1000)
        )

class EditorTutorial(CustomCutsceneBase):
    def init_blocks(self):
        self.add_block(
            SetCharacter("baby","happy"),
            Wait(500),
            Say("This is the editor screen !\nPress the 'q' key to enter the tile picker !","baby","happy"),
            Wait(500),
        )


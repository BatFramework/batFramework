import batFramework as bf
from .transition import Transition
from typing import Callable,Any

class Cutscene:
    def __init__(self):
        """
        Create a base Cutscene (ends immediately)
        """

    def start(self):
        """
        Called by the manager or the parent cutscene
        Has to return to blank init state
        """
        self.end()

    def process_event(self,event):
        pass
            
    def update(self,dt):
        pass

    def __str__(self)->str:
        return self.__class__.__name__

    def end(self):
        """
        Mark self as over
        """
        print("Start ",self)

        self.is_over = True

class Sequence(Cutscene):
    def __init__(self,*cutscenes):
        self.sub_cutscenes :list[Cutscene] = list(cutscenes)
        self.index = 0

    def start(self):
        self.is_over = False
        self.index = 0
        if self.sub_cutscenes:
            self.sub_cutscenes[0].start()

    def process_event(self,event):
        """
        propagate process event for current sub cutscene
        """
        if self.index >0 and not self.is_over:
            self.sub_cutscenes[self.index].process_event(event)

        

    def update(self,dt):
        """
        Update current sub cutscene (if any)
        if current is over, start next one
        if current was last, then end self
        """
        if self.index < len(self.sub_cutscenes):
            self.sub_cutscenes[self.index].update(dt)
            if self.sub_cutscenes[self.index].is_over:
                self.index += 1
                if self.index == len(self.sub_cutscenes):
                    self.end()
                    return
                self.sub_cutscenes[self.index].start()


class Parallel(Cutscene):
    def __init__(self,*cutscenes:Cutscene):
        self.sub_cutscenes : list[Cutscene] = list(cutscenes) 

    def start(self):
        self.is_over = False
        if not self.sub_cutscenes:
            self.end()
        for s in self.sub_cutscenes:
            s.start()        

    def update(self,dt):
        for s in self.sub_cutscenes:
            s.update(dt)
        if all(s.is_over for s in self.sub_cutscenes):
            self.end()

class Wait(Cutscene):
    def __init__(self,duration:float,scene_name:str="global"):
        self.duration = duration
        self.scene_name = scene_name
    def start(self):
        self.is_over = False
        self.timer = bf.SceneTimer(duration=self.duration,end_callback=self.end,scene_name=self.scene_name)
        self.timer.start()



class TransitionToScene(Cutscene):
    def __init__(self,scene_name:str,transition:Transition):
        self.scene_name = scene_name
        self.transition: Transition = transition

    def start(self):
        self.is_over = False
        bf.CutsceneManager().manager.transition_to_scene(self.scene_name,self.transition)
        bf.Timer(self.transition.duration,end_callback=self.end).start()






class GlideWorldCameraFromTo(Cutscene):
    def __init__(self,start:tuple[float,float], stop:tuple[float,float],duration:float=1,easing:bf.easing=bf.easing.EASE_IN_OUT,scene_name:str=None):
        super().__init__()
        self.scene =  None
        self.scene_name = scene_name
        self.start_pos = start
        self.stop_pos = stop
        self.controller = bf.EasingController(duration,easing,update_callback=self.internal,end_callback=self.end)


    def start(self):
        self.is_over = False
        if self.scene_name is None:
            self.scene_name = bf.CutsceneManager().manager.get_scene_at(0).name

        self.scene = bf.CutsceneManager().manager.get_scene(self.scene_name)
        self.controller.start()


    def internal(self,progression:float):
        if not self.scene: 
            self.end()
            return
        self.scene.camera.set_center(
            self.start_pos[0]+progression*(self.stop_pos[0]-self.start_pos[0]),
            self.start_pos[1]+progression*(self.stop_pos[1]-self.start_pos[1])
        )

    def end(self):
        if self.scene:
            self.scene.camera.set_center(self.stop_pos[0],self.stop_pos[1])
        
        super().end()



class Function(Cutscene):
    def __init__(self, function:Callable[[],Any],*args,**kwargs):
        super().__init__()
        self.function:Callable[[],Any] = function
        self.args = args
        self.kwargs = kwargs
        
    def start(self):
        self.is_over = False
        self.function(*self.args,**self.kwargs)
        self.end()

class GlideCamera(Cutscene):
    def __init__(
        self,
        start: tuple[float, float] | None,
        stop: tuple[float, float] | None,
        duration: float = 1,
        easing: bf.easing = bf.easing.EASE_IN_OUT,
        scene_name: str | None = None,
        layer_name: str = "world",
    ):
        """
        If start is None, it will be defaulted to the current camera center position.
        Stop must be provided
        """
        super().__init__()
        self.scene = None
        self.layer = None
        self.scene_name = scene_name
        self.layer_name = layer_name
        self.start_pos = start
        self.stop_pos = stop
        self.controller = bf.EasingController(
            duration, easing, update_callback=self.internal, end_callback=self.end
        )

    def start(self):
        self.is_over = False

        if self.scene_name is None:
            self.scene_name = bf.CutsceneManager().manager.get_scene_at(0).name

        self.scene = bf.CutsceneManager().manager.get_scene(self.scene_name)
        self.layer = self.scene.get_layer(self.layer_name)

        if not self.layer:
            raise ValueError(f"Layer '{self.layer_name}' not found in scene '{self.scene_name}'.")

        # Fallback to current camera position
        if self.start_pos is None:
            self.start_pos = self.layer.camera.get_center()

        self.controller.start()

    def internal(self, progression: float):
        self.layer.camera.set_center(
            self.start_pos[0] + progression * (self.stop_pos[0] - self.start_pos[0]),
            self.start_pos[1] + progression * (self.stop_pos[1] - self.start_pos[1]),
        )

    def end(self):
        if self.layer:
            self.layer.camera.set_center(*self.stop_pos)
        super().end()


        
class GlideCameraBy(GlideCamera):
    def __init__(
        self,
        delta: tuple[float, float],
        duration: float = 1,
        easing: bf.easing = bf.easing.EASE_IN_OUT,
        scene_name: str | None = None,
        layer_name: str = "world",
    ):
        stop_pos = (
            start_pos[0] + self.delta[0],
            start_pos[1] + self.delta[1],
        )
        super().__init__(
            start=None,
            stop=None,
            delta=delta,
            duration=duration,
            easing=easing,
            scene_name=scene_name,
            layer_name=layer_name,
        )

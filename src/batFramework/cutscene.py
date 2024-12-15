import batFramework as bf
from .transition import Transition
class Cutscene:
    def __init__(self,*cutscenes):
        self.is_over : bool = False
        self.sub_cutscenes : list[Cutscene] = list(cutscenes)
        self.sub_index = -1

    def start(self):
        if self.sub_cutscenes:
            self.sub_index = 0
            self.sub_cutscenes[self.sub_index].start()
        else:
            self.end()

    def process_event(self,event):
        if self.sub_index > 0: 
            self.sub_cutscenes[self.sub_index].process_event(event)
            
    def update(self,dt):
        if self.sub_index >= 0: 
            self.sub_cutscenes[self.sub_index].update(dt)
            if self.sub_cutscenes[self.sub_index].is_over:
                self.sub_index +=1
                if self.sub_index >= len(self.sub_cutscenes):
                    self.end()
                    return
                self.sub_cutscenes[self.sub_index].start()
            
    def end(self):
        self.is_over = True


class Wait(Cutscene):
    def __init__(self,duration:float,scene_name:str="global"):
        super().__init__()
        self.duration = duration
        self.scene_name = scene_name
    def start(self):
        self.timer = bf.SceneTimer(duration=self.duration,end_callback=self.end,scene_name=self.scene_name)
        self.timer.start()



class TransitionToScene(Cutscene):
    def __init__(self,scene_name:str,transition:Transition):
        super().__init__()
        self.scene_name = scene_name
        self.transition: Transition = transition

    def start(self):
        bf.CutsceneManager().manager.transition_to_scene(self.scene_name,self.transition)
        bf.Timer(self.transition.duration,end_callback=self.end).start()



class GlideWorldCameraTo(Cutscene):
    def __init__(self, stop:tuple[float,float],duration:float=1,easing:bf.easing=bf.easing.EASE_IN_OUT,scene_name:str=None):
        super().__init__()
        self.scene =  None
        self.scene_name = scene_name
        self.stop_pos = stop
        self.start_pos = None
        self.controller = bf.EasingController(easing,duration,update_callback=self.internal,end_callback=self.end)


    def start(self):
        if self.scene_name is None:
            self.scene_name = bf.CutsceneManager().manager.get_scene_at(0).name

        self.scene = bf.CutsceneManager().manager.get_scene(self.scene_name)
        self.start_pos = self.scene.camera.get_center()
        self.controller.start()


    def internal(self,progression:float):
        self.scene.camera.set_center(
            self.start_pos[0]+progression*(self.stop_pos[0]-self.start_pos[0]),
            self.start_pos[1]+progression*(self.stop_pos[1]-self.start_pos[1])

        )

    def end(self):
        if self.scene:
            self.scene.camera.set_center(self.stop_pos[0],self.stop_pos[1])
        
        super().end()


class GlideWorldCameraFromTo(Cutscene):
    def __init__(self,start:tuple[float,float], stop:tuple[float,float],duration:float=1,easing:bf.easing=bf.easing.EASE_IN_OUT,scene_name:str=None):
        super().__init__()
        self.scene =  None
        self.scene_name = scene_name
        self.start_pos = start
        self.stop_pos = stop
        self.controller = bf.EasingController(easing,duration,update_callback=self.internal,end_callback=self.end)


    def start(self):
        if self.scene_name is None:
            self.scene_name = bf.CutsceneManager().manager.get_scene_at(0).name

        self.scene = bf.CutsceneManager().manager.get_scene(self.scene_name)
        self.controller.start()


    def internal(self,progression:float):
        self.scene.camera.set_center(
            self.start_pos[0]+progression*(self.stop_pos[0]-self.start_pos[0]),
            self.start_pos[1]+progression*(self.stop_pos[1]-self.start_pos[1])

        )

    def end(self):
        if self.scene:
            self.scene.camera.set_center(self.stop_pos[0],self.stop_pos[1])
        
        super().end()

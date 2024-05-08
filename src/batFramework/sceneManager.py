import batFramework as bf
import pygame

def swap(lst,index1,index2):
    lst[index1],lst[index2] = lst[index2],lst[index1]  


class SceneManager:
    def __init__(self, *initial_scenes: bf.Scene) -> None:
        self._debugging :int = 0
        self._sharedVarDict : dict = {}

        self._scene_transitions: list[bf.transition.Transition] = []
        self.set_sharedVar("debugging_mode",self._debugging)
        self.set_sharedVar("in_cutscene", False)
        self.current_transition : dict[str,bf.transition.Transition]= {}
        self.set_sharedVar("player_has_control", True)
        self.last_frame = None

        self._scenes: list[bf.Scene] = list(initial_scenes)
        for index, s in enumerate(self._scenes):
            s.set_manager(self)
            s.set_scene_index(index)
            s.do_when_added()
        self.set_scene(initial_scenes[0].get_name())
        self.update_scene_states()

        self.shared_events = [pygame.WINDOWRESIZED]


    def print_status(self):
        print("-" * 40)
        print([(s._name, "Active" if s._active else "Inactive","Visible" if s._visible else "Invisible", f"index={s.scene_index}") for s in self._scenes])
        print(f"[Debugging] = {self._debugging}")
        print("---SHARED VARIABLES---")
        for name, value in self._sharedVarDict.items():
            print(f"[{str(name)} = {str(value)}]")
        print("-" * 40)

    def set_sharedVar(self, name, value) -> bool:
        self._sharedVarDict[name] = value
        return True

    def get_sharedVar(self, name,error_value=None):
        if name not in self._sharedVarDict:
            return error_value
        return self._sharedVarDict[name]

    def get_current_scene_name(self) -> str:
        return self._scenes[0].get_name()

    def get_current_scene(self) -> bf.Scene:
        return self._scenes[0]

    def update_scene_states(self):
        self.active_scenes = [s for s in reversed(self._scenes) if s._active]
        self.visible_scenes = [s for s in reversed(self._scenes) if s._visible]

    def add_scene(self, scene: bf.Scene):
        if scene in self._scenes and not self.has_scene(scene._name):
            return
        scene.set_manager(self)
        scene.do_when_added()
        self._scenes.insert(0, scene)

    def remove_scene(self, name: str):
        self._scenes = [s for s in self._scenes if s._name != name]

    def has_scene(self, name):
        return any(name == scene._name for scene in self._scenes)

    def get_scene(self, name):
        if not self.has_scene(name):
            return None
        for scene in self._scenes:
            if scene._name == name:
                return scene

    def get_scene_at(self,index:int)->bf.Scene|None:
        if index < 0 or index >= len(self._scenes) : return None
        return self._scenes[index]

    def transition_to_scene(self,scene_name: str,transition : bf.transition.Transition = bf.transition.Fade(0.1) ,index: int=0):
        target_scene = self.get_scene(scene_name)
        if (
            len(self._scenes) == 0
            or not target_scene
            or index >= len(self._scenes)
            or index < 0
        ):
            return
        source_surface = bf.const.SCREEN.copy()
        dest_surface = bf.const.SCREEN.copy()

        # self.draw(source_surface)
        target_scene.draw(dest_surface)
        
        self.current_transition = {"scene_name":scene_name,"transition":transition}
        transition.set_start_callback(lambda : self._start_transition(target_scene))
        transition.set_end_callback(lambda : self._end_transition(scene_name,index))
        transition.set_source(source_surface)
        transition.set_dest(dest_surface)
        transition.start()

    def _start_transition(self,target_scene):
        target_scene.set_active(True)
        target_scene.set_visible(True)
        self.set_sharedVar("player_has_control",False)

    def _end_transition(self,scene_name,index):
        self.set_scene(scene_name,index)
        self.set_sharedVar("player_has_control",True)
        self.current_transition.clear()
        
    def set_scene(self, scene_name, index=0):
        if (len(self._scenes) == 0
            or (target_scene := self.get_scene(scene_name) ) is None
            or index >= len(self._scenes) or index < 0):
            return
            
        # switch
        self._scenes[index].on_exit()
        #re-insert scene at index 0
        self._scenes.remove(target_scene)
        self._scenes.insert(index,target_scene)
        _ = [s.set_scene_index(i) for i, s in enumerate(self._scenes)]
        target_scene.on_enter()


    def process_event(self, event: pygame.Event):
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_LCTRL] and event.type == pygame.KEYDOWN):
            if (event.key == pygame.K_d):
                self._debugging = (self._debugging + 1) % 4
                self.set_sharedVar("debugging_mode",self._debugging)
                return
            if (event.key == pygame.K_p):
                self.print_status()
                return
        if event.type in self.shared_events:
            [s.process_event(event) for s in self._scenes]
        else:
            self._scenes[0].process_event(event)
        
    def update(self, dt: float) -> None:
        for scene in self.active_scenes:
            scene.update(dt)
        self.do_update(dt)

    def do_update(self, dt: float):
        pass

    def draw(self, surface) -> None:
        for scene in self.visible_scenes:
            scene.draw(surface)
        if self.current_transition:
            self._draw_transition(surface)

    def _draw_transition(self,surface):
        self.current_transition["transition"].set_source(surface)
        tmp = bf.const.SCREEN.copy()
        self.get_scene(self.current_transition["scene_name"]).draw(tmp)
        self.current_transition["transition"].set_dest(tmp)
        self.current_transition["transition"].draw(surface)
        return

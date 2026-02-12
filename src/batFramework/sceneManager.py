import batFramework as bf
import pygame
from typing import Self

def swap(lst, index1, index2):
    lst[index1], lst[index2] = lst[index2], lst[index1]


class SceneManager:
    def __init__(self) -> None:
        self.scenes: list[bf.BaseScene] = []
        self.shared_events = {pygame.WINDOWRESIZED}
        self.current_transition : tuple[str,bf.transition.Transition,int] | None= None

    def init_scenes(self, *initial_scenes:bf.Scene):
        for index, s in enumerate(initial_scenes):
            s.set_scene_index(index)
        for s in reversed(initial_scenes):
            self.add_scene(s)
        self.set_scene(initial_scenes[0].get_name())
        self.update_scene_states()

    def set_shared_event(self, event: pygame.Event) -> None:
        """
        Add an event that will be propagated to all active scenes, not just the one on top.
        """
        self.shared_events.add(event)

    def print_status(self):
        """
        Print detailed information about the current state of the scenes and shared variables.
        """

        def format_scene_info(scene:bf.Scene):
            status = 'Active' if scene.active else 'Inactive'
            visibility = 'Visible' if scene.visible else 'Invisible'
            return f"{scene.name:<30} | {status:<8} | {visibility:<10} | Index={scene.scene_index}"

        def format_shared_variable(name, value):
            return f"[{name}] = {value}"

        print("\n" + "=" * 50)
        print(" SCENE STATUS".center(50))
        print("=" * 50)

        # Print scene information
        if self.scenes:
            header = f"{'Scene Name':<30} | {'Status':<8} | {'Visibility':<10} | {'Index':<7}"
            print(header)
            print("-" * 50)
            print("\n".join(format_scene_info(s) for s in self.scenes))
        else:
            print("No scenes available.")

        # Print debugging mode status
        print("\n" + "=" * 50)
        print(" DEBUGGING STATUS".center(50))
        print("=" * 50)
        print(f"[Debugging Mode] = {bf.ResourceManager().get_sharedVar('debug_mode')}")

        # Print shared variables
        print("\n" + "=" * 50)
        print(" SHARED VARIABLES".center(50))
        print("=" * 50)

        if bf.ResourceManager().shared_variables:
            for name, value in bf.ResourceManager().shared_variables.items():
                print(format_shared_variable(name, value))
        else:
            print("No shared variables available.")

        print("=" * 50 + "\n")

    def get_current_scene_name(self) -> str:
        """get the name of the current scene"""
        return self.scenes[0].get_name()

    def get_current_scene(self) -> bf.Scene:
        return self.scenes[0]

    def update_scene_states(self):
        self.active_scenes = [s for s in reversed(self.scenes) if s.active]
        self.visible_scenes = [s for s in reversed(self.scenes) if s.visible]

    def add_scene(self, scene: bf.Scene):
        if scene in self.scenes and not self.has_scene(scene.name):
            return
        scene.set_manager(self)
        scene.when_added()
        self.scenes.insert(0, scene)

    def remove_scene(self, name: str):
        self.scenes = [s for s in self.scenes if s.name != name]

    def has_scene(self, name:str):
        return any(name == scene.name for scene in self.scenes)

    def get_scene(self, name:str):
        if not self.has_scene(name):
            return None
        for scene in self.scenes:
            if scene.name == name:
                return scene

    def get_scene_at(self, index: int) -> bf.Scene | None:
        if index < 0 or index >= len(self.scenes):
            return None
        return self.scenes[index]

    def transition_to_scene(
        self,
        scene_name: str,
        transition: bf.transition.Transition = None,
        index: int = 0,
    ):
        if transition is None:
            transition = bf.transition.Fade(0.1)
        if not (target_scene := self.get_scene(scene_name)):
            print(f"Scene '{scene_name}' does not exist")
            return
        if not (source_scene := self.get_scene_at(index)):
            print(f"No scene exists at index {index}.")
            return       
        
        source_surface = bf.const.SCREEN.copy()
        dest_surface = bf.const.SCREEN.copy()

        target_scene.draw(dest_surface) # draw at least once to ensure smooth transition
        target_scene.set_active(True)
        target_scene.set_visible(True)

        target_scene.do_on_enter_early() 
        source_scene.do_on_exit_early()

        self.current_transition :tuple[str,bf.transition.Transition]=(scene_name,transition,index)
        transition.set_source(source_surface)
        transition.set_dest(dest_surface)
        transition.start()



    def set_scene(self, scene_name, index=0, ignore_early: bool = False):
        target_scene = self.get_scene(scene_name)
        if not target_scene:
            print(f"'{scene_name}' does not exist")
            return
        if len(self.scenes) == 0 or index >= len(self.scenes) or index < 0:
            return

        # switch
        if not ignore_early:
            self.scenes[index].do_on_exit_early()
        self.scenes[index].on_exit()
        # re-insert scene at index 0
        self.scenes.remove(target_scene)
        self.scenes.insert(index, target_scene)
        _ = [s.set_scene_index(i) for i, s in enumerate(self.scenes)]
        if not ignore_early:
            self.scenes[index].do_on_enter_early()
        target_scene.on_enter()



    def cycle_debug_mode(self):
        current_index = bf.ResourceManager().get_sharedVar("debug_mode").value
        next_index = (current_index + 1) % len(bf.debugMode)
        bf.ResourceManager().set_sharedVar("debug_mode", bf.debugMode(next_index))
        return bf.debugMode(next_index)
    
    def set_debug_mode(self,debugMode : bf.debugMode):
        bf.ResourceManager().set_sharedVar("debug_mode", debugMode)

    def process_event(self, event: pygame.Event):

        if event.type in self.shared_events:
            [s.process_event(event) for s in self.scenes]
        else:
            self.scenes[0].process_event(event)

    def update(self, dt: float) -> None:
        for scene in self.active_scenes:
            scene.update(dt)
        if self.current_transition and self.current_transition[1].is_over:
            self.set_scene(self.current_transition[0],self.current_transition[2],True)
            self.current_transition = None
        self.do_update(dt)

    def do_update(self, dt: float):
        pass

    def draw(self, surface:pygame.Surface) -> None:
        for scene in self.visible_scenes:
            scene.draw(surface)
        if self.current_transition is not None:
            self.current_transition[1].set_source(surface)
            tmp = surface.copy()
            self.get_scene(self.current_transition[0]).draw(tmp)
            self.current_transition[1].set_dest(tmp)
            self.current_transition[1].draw(surface)


import batFramework as bf
import pygame
from typing import Self

def swap(lst, index1, index2):
    lst[index1], lst[index2] = lst[index2], lst[index1]


class SceneManager:
    def __init__(self) -> None:
        self.scenes: list[bf.Scene] = []
        self.shared_variables: dict = {}
        self.shared_events = {pygame.WINDOWRESIZED}

        self.set_sharedVar("in_cutscene", False)
        self.set_sharedVar("player_has_control", True)

        self.debug_mode: bf.enums.debugMode = bf.debugMode.HIDDEN
        self.current_transitions: dict[str, bf.transition.Transition] = {}



    def init_scenes(self,*initial_scenes):
        for index, s in enumerate(initial_scenes):
            s.set_scene_index(index)
        for s in reversed(initial_scenes):
            self.add_scene(s)
        # self.scenes = list(initial_scenes)
        self.set_scene(initial_scenes[0].get_name())
        self.update_scene_states()

    def set_shared_event(self,event:pygame.Event)->None:
        """
        Add an event that will be propagated to all active scenes, not just the one on top.
        """
        self.shared_events.add(event)

    def print_status(self):
        """
        Print some information about the current state of the scenes.
        """
        print("-" * 40)
        print(
            '\n'.join(
                f" {s.name:<30}\t{'Active' if s.active else 'Inactive'}\t{'Visible' if s.visible else 'Invisible'}\tindex= {s.scene_index}"
                for s in self.scenes
            )
        )
        print(f"[Debugging] = {self.debug_mode}")
        print("---SHARED VARIABLES---")
        for name, value in self.shared_variables.items():
            print(f"[{str(name)} = {str(value)}]")
        print("-" * 40)

    def set_sharedVar(self, name, value) -> bool:
        """
        Set a shared variable of any type. This will be accessible (read/write) from any scene
        """
        self.shared_variables[name] = value
        return True

    def get_sharedVar(self, name, error_value=None):
        """
        Get a shared variable
        """
        return self.shared_variables.get(name,error_value)

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
        scene.do_when_added()
        self.scenes.insert(0, scene)

    def remove_scene(self, name: str):
        self.scenes = [s for s in self.scenes if s.name != name]

    def has_scene(self, name):
        return any(name == scene.name for scene in self.scenes)

    def get_scene(self, name):
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
        transition: bf.transition.Transition = bf.transition.Fade(0.1),
        index: int = 0,
    ):
        target_scene = self.get_scene(scene_name)
        if not target_scene : 
            print(f"Scene '{scene_name}' does not exist")
            return
        if (
            len(self.scenes) == 0
            or index >= len(self.scenes)
            or index < 0
        ):
            return
        source_surface = bf.const.SCREEN.copy()
        dest_surface = bf.const.SCREEN.copy()

        # self.draw(source_surface)
        target_scene.draw(dest_surface)
        target_scene.do_on_enter_early()
        self.get_scene_at(index).do_on_exit_early()
        self.current_transitions = {"scene_name": scene_name, "transition": transition}
        transition.set_start_callback(lambda: self._start_transition(target_scene))
        transition.set_end_callback(lambda: self._end_transition(scene_name, index))
        transition.set_source(source_surface)
        transition.set_dest(dest_surface)
        transition.start()

    def _start_transition(self, target_scene: bf.Scene):
        target_scene.set_active(True)
        target_scene.set_visible(True)
        self.set_sharedVar("player_has_control", False)

    def _end_transition(self, scene_name, index):
        self.set_scene(scene_name, index)
        self.set_sharedVar("player_has_control", True)
        self.current_transitions.clear()

    def set_scene(self, scene_name, index=0):
        target_scene = self.get_scene(scene_name)
        if not target_scene : 
            print(f"'{scene_name}' does not exist")
            return
        if (
            len(self.scenes) == 0
            or index >= len(self.scenes)
            or index < 0
        ):
            return

        # switch
        self.scenes[index].on_exit()
        # re-insert scene at index 0
        self.scenes.remove(target_scene)
        self.scenes.insert(index, target_scene)
        _ = [s.set_scene_index(i) for i, s in enumerate(self.scenes)]
        target_scene.on_enter()

    def cycle_debug_mode(self):
        current_index = self.debug_mode.value
        next_index = (current_index + 1) % len(bf.debugMode)
        return bf.debugMode(next_index)

    def process_event(self, event: pygame.Event):
        keys = pygame.key.get_pressed()
        if (
            keys[pygame.K_LCTRL]
            and keys[pygame.K_LSHIFT]
            and event.type == pygame.KEYDOWN
        ):
            if event.key == pygame.K_d:
                self.debug_mode = self.cycle_debug_mode()
                self.set_sharedVar("debug_mode", self.debug_mode)
                return
            if event.key == pygame.K_p:
                self.print_status()
                return
        if event.type in self.shared_events:
            [s.process_event(event) for s in self.scenes]
        else:
            self.scenes[0].process_event(event)

    def update(self, dt: float) -> None:
        for scene in self.active_scenes:
            scene.update(dt)
        self.do_update(dt)

    def do_update(self, dt: float):
        pass

    def draw(self, surface) -> None:
        for scene in self.visible_scenes:
            scene.draw(surface)
        if self.current_transitions:
            self._draw_transition(surface)

    def _draw_transition(self, surface):
        self.current_transitions["transition"].set_source(surface)
        tmp = bf.const.SCREEN.copy()
        self.get_scene(self.current_transitions["scene_name"]).draw(tmp)
        self.current_transitions["transition"].set_dest(tmp)
        self.current_transitions["transition"].draw(surface)
        return

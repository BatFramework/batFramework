import batFramework as bf
import pygame


class SceneManager:
    def __init__(self, *initial_scenes: bf.Scene) -> None:
        self._debugging = 0
        self.sharedVarDict = {}

        self.transitions: list[bf.BaseTransition] = []
        self.set_sharedVar("debugging_mode",self._debugging)
        self.set_sharedVar("in_cutscene", False)

        self._scenes: list[bf.Scene] = list(initial_scenes)
        for index, s in enumerate(self._scenes):
            s.set_manager(self)
            s.set_scene_index(index)
            s.do_when_added()
        self.set_scene(self._scenes[0]._name)
        self.update_scene_states()

    def print_status(self):
        print("-" * 40)
        print([(s._name, s._active, s._visible, s.scene_index) for s in self._scenes])
        print(f"[Debugging] = {self._debugging}")
        print("---SHARED VARIABLES---")
        _ = [
            print(f"[{str(name)} = {str(value)}]")
            for name, value in self.sharedVarDict.items()
        ]
        print("-" * 40)

    def set_sharedVar(self, name, value) -> bool:
        self.sharedVarDict[name] = value
        return True

    def get_sharedVar(self, name):
        if name not in self.sharedVarDict:
            return None
        return self.sharedVarDict[name]

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

    def transition_to_scene(self, dest_scene_name, transition, **kwargs):
        self.set_scene(dest_scene_name)

    def set_scene(self, name, index=0):
        if (
            len(self._scenes) == 0
            or not self.has_scene(name)
            or index >= len(self._scenes)
        ):
            return

        target_scene = self.get_scene(name)
        if not target_scene : return
        old_scene = self._scenes[index]
        # switch
        old_scene.on_exit()
        self.remove_scene(name)
        self._scenes.insert(index, target_scene)
        _ = [s.set_scene_index(i) for i, s in enumerate(self._scenes)]
        target_scene.on_enter()

    def process_event(self, event: pygame.Event):
        keys = pygame.key.get_pressed()
        if (
            keys[pygame.K_LCTRL]
            and event.type == pygame.KEYDOWN
            and event.key == pygame.K_d
        ):
            self._debugging = (self._debugging + 1) % 4
            self.set_sharedVar("debugging_mode",self._debugging)

            return
        if (
            keys[pygame.K_LCTRL]
            and event.type == pygame.KEYDOWN
            and event.key == pygame.K_p
        ):
            self.print_status()
            return
        self._scenes[0].process_event(event)

    def update(self, dt: float) -> None:
        for scene in self.active_scenes:
            scene.update(dt)
        self.do_update(dt)

    def do_update(self, dt: float):
        return

    def draw(self, surface) -> None:
        for scene in self.visible_scenes:
            scene.draw(surface)

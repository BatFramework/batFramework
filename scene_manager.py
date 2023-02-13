import pygame

from .scene import Scene
from .transition import Transition


class SceneManager:
    def __init__(self, gameManagerLink) -> None:
        self._scenes: dict[str, Scene] = {}
        self._sceneList: list[str] = []
        self._currentScene: str = ""
        self._previousScene: str = ""
        self._gameManagerLink = gameManagerLink

    def info(self):
        title = "SCENE MANAGER OUTPUT"

        print(f"{title:-^48}")
        print("current scene : ", self._currentScene)
        print("previous scene :", self._previousScene)
        for scene in self._sceneList:
            print(
                f" {scene} ; {self.get_scene(scene).is_active()} ; {self.get_scene(scene).is_visible()} ; {'[CURRENT]' if scene == self._currentScene else ''}"
            )
        print(f'{"END":-^48}')

    def get_previous_scene(self):
        return self._previousScene

    def is_empty(self) -> bool:
        return not self._scenes

    def get_active_scenes(self) -> list[str]:
        return [name for name in self._sceneList if self._scenes[name].is_active()]

    def get_visible_scenes(self) -> list[str]:
        return [name for name in self._sceneList if self._scenes[name].is_visible()]

    def get_scene(self, name: str) -> Scene:
        if name not in self._sceneList:
            print(f"{name} is not a scene")
            return None

        return self._scenes[name]

    def remove_scene(self, name: str):
        if name not in self._sceneList:
            return False
        self._sceneList = [i for i in self._sceneList if i != name]
        self._scenes.pop(name)

    # name must and will be in capital letters
    def add_scene(self, name: str, scene: Scene):
        name = name.upper()

        scene.set_id(name)
        scene.set_active(False)
        scene.set_visible(False)
        scene.set_game_manager_link(self._gameManagerLink)
        scene.set_scene_manager_link(self)

        self._sceneList.append(name)
        if self.is_empty():
            self._scenes[name] = scene
            self.set_scene(name)
        else:
            self._scenes[name] = scene

    def on_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN:
            self.get_scene(self.get_active_scenes()[-1])._on_key_down(event.key)
        elif event.type == pygame.KEYUP:
            self.get_scene(self.get_active_scenes()[-1])._on_key_up(event.key)
        else:
            self.get_scene(self.get_active_scenes()[-1])._on_event(event)

    def transition_to_scene(self, transition: Transition, dest: str):
        dest = dest.upper()

        if dest not in self._sceneList:
            print("Scene", dest, "does not exist")
            exit(1)
        transition.set_game_manager_link(self._gameManagerLink)
        transition.set_scene_manager_link(self)
        transition.set_dest(self.get_scene(dest))
        transition.set_source(self.get_scene(self._currentScene))
        self.add_scene(transition.get_id(), transition)
        self.set_scene(transition.get_id())

    def set_scene(self, name: str):
        name = name.upper()

        if name not in self._sceneList:
            print("Scene", name, "does not exist")
            exit(1)

        if self._currentScene != "":
            self.get_scene(self._currentScene).on_exit()
        self._previousScene = self._currentScene
        self._currentScene = name

        self.get_scene(self._currentScene).set_active(True)
        self.get_scene(self._currentScene).set_visible(True)
        self.get_scene(self._currentScene).on_enter()
        self._sceneList.append(
            self._sceneList.pop(self._sceneList.index(self._currentScene))
        )

    def update(self, dt: float) -> None:
        self._scenes[self.get_active_scenes()[-1]]._update(dt)

    def draw(self, surface: pygame.Surface):
        for scene in self.get_visible_scenes():
            self._scenes[scene].draw(surface)

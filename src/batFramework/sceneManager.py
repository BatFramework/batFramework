import batFramework as bf
import logging
import pygame
from typing import Self

logger = logging.getLogger(__name__)

def swap(lst, index1, index2):
    lst[index1], lst[index2] = lst[index2], lst[index1]


class SceneManager:
    def __init__(self) -> None:
        self.scenes: list[bf.Scene] = []
        # Every scene owns cameras that must follow a physical window resize,
        # including scenes underneath the currently active one.
        self.shared_events = {pygame.VIDEORESIZE, pygame.WINDOWRESIZED}
        self.current_transition: tuple[str, bf.transition.Transition, int] | None = None
        bf.Context.debug_mode = bf.debugMode.HIDDEN

    def init_scenes(self, *initial_scenes: bf.Scene):
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
        Log detailed information about the current state of the scenes and shared variables.
        """
        logger.info(self.get_status())

    def get_status(self) -> str:
        """
        Return detailed information about the current state of the scenes and shared variables.
        """

        def format_scene_info(scene: bf.Scene):
            status = "Active" if scene.active else "Inactive"
            visibility = "Visible" if scene.visible else "Invisible"
            return f"{scene.name:<30} | {status:<8} | {visibility:<10} | Index={scene.scene_index}"

        def format_shared_variable(name, value):
            return f"[{name}] = {value}"

        lines = []
        lines.append("\n" + "=" * 50)
        lines.append(" SCENE STATUS".center(50))
        lines.append("=" * 50)

        # scene information
        if self.scenes:
            header = f"{'Scene Name':<30} | {'Status':<8} | {'Visibility':<10} | {'Index':<7}"
            lines.append(header)
            lines.append("-" * 50)
            lines.append("\n".join(format_scene_info(s) for s in self.scenes))
        else:
            lines.append("No scenes available.")

        # debugging mode status
        lines.append("\n" + "=" * 50)
        lines.append(" DEBUGGING STATUS".center(50))
        lines.append("=" * 50)
        lines.append(f"[Debugging Mode] = {bf.Context.debug_mode.name}")

        # shared variables
        lines.append("\n" + "=" * 50)
        lines.append(" SHARED VARIABLES".center(50))
        lines.append("=" * 50)

        if bf.ResourceManager().shared_variables:
            for name, value in bf.ResourceManager().shared_variables.items():
                lines.append(format_shared_variable(name, value))
        else:
            lines.append("No shared variables available.")

        lines.append("=" * 50 + "\n")
        return "\n".join(lines)

    def get_current_scene_name(self) -> str:
        """get the name of the current scene"""
        return self.scenes[0].get_name()

    def get_current_scene(self) -> bf.Scene:
        return self.scenes[0]

    def update_scene_states(self):
        self.active_scenes = [s for s in reversed(self.scenes) if s.active]
        self.visible_scenes = [s for s in reversed(self.scenes) if s.visible]

    def add_scene(self, scene: bf.Scene):
        if self.has_scene(scene.name):
            return
        scene.set_manager(self)
        scene.when_added()
        self.scenes.insert(0, scene)

    def remove_scene(self, name: str):
        self.scenes = [s for s in self.scenes if s.name != name]

    def has_scene(self, name: str):
        return any(name == scene.name for scene in self.scenes)

    def get_scene(self, name: str):
        for scene in self.scenes:
            if scene.name == name:
                return scene
        return None
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
            logger.warning(f"Scene '{scene_name}' does not exist")
            return
        if not (source_scene := self.get_scene_at(index)):
            logger.warning(f"No scene exists at index {index}.")
            return

        source_surface = bf.const.SCREEN.copy()
        dest_surface = bf.const.SCREEN.copy()

        target_scene.draw(
            dest_surface
        )  # draw at least once to ensure smooth transition
        target_scene.set_active(True)
        target_scene.set_visible(True)

        target_scene.do_on_enter_early()
        source_scene.do_on_exit_early()

        self.current_transition: tuple[str, bf.transition.Transition] = (
            scene_name,
            transition,
            index,
        )
        transition.set_source(source_surface)
        transition.set_dest(dest_surface)
        transition.start()

    def set_scene(self, scene_name, index=0, ignore_early: bool = False, source_target_state:tuple=None,dest_target_state:tuple=None):
        """
        ignore_early skips the do_on_exit_early method of the origin scene
        as well as the do_on_enter_early of the target scene
        """
        target_scene = self.get_scene(scene_name)
        if not target_scene:
            logger.warning(f"Scene '{scene_name}' does not exist")
            return
        if len(self.scenes) == 0 or index >= len(self.scenes) or index < 0:
            return
        # switch
        if not ignore_early:
            self.scenes[index].do_on_exit_early()
        self.scenes[index].on_exit()

        if source_target_state is None:
            source_target_state = False,False        
        self.scenes[index].set_active(source_target_state[0])
        self.scenes[index].set_visible(source_target_state[1])



        # re-insert scene at index 0
        self.scenes.remove(target_scene)
        self.scenes.insert(index, target_scene)
        _ = [s.set_scene_index(i) for i, s in enumerate(self.scenes)]
        if not ignore_early:
            self.scenes[index].do_on_enter_early()
        target_scene.on_enter()

        if dest_target_state is None:
            dest_target_state = True,True        
        target_scene.set_active(dest_target_state[0])
        target_scene.set_visible(dest_target_state[1])

    def cycle_debug_mode(self)-> bf.debugMode:
        current_index = bf.Context.debug_mode.value
        next_debug_mode =  bf.debugMode((current_index + 1) % len(bf.debugMode))
        self.set_debug_mode(next_debug_mode)
        return next_debug_mode

    def set_debug_mode(self, debugMode: bf.debugMode):
        pygame.event.post(pygame.event.Event(bf.const.DEBUG_MODE_CHANGE_EVENT, {"mode": debugMode}))
        bf.Context.debug_mode = debugMode

    def process_event(self, event: pygame.Event):

        if event.type in self.shared_events:
            [s.process_event(event) for s in self.scenes]
        else:
            self.scenes[0].process_event(event)

    def update(self, dt: float) -> None:
        for scene in self.active_scenes:
            bf.Context.current_scene = scene.name
            scene.update(dt)
        bf.Context.current_scene = None
        if self.current_transition and self.current_transition[1].is_over:
            self.set_scene(self.current_transition[0], self.current_transition[2], True)
            self.current_transition = None
        self.do_update(dt)

    def do_update(self, dt: float):
        pass

    def draw(self, surface: pygame.Surface) -> None:
        for scene in self.visible_scenes:
            bf.Context.current_scene = scene.name
            bf.Context.current_camera = scene.camera
            scene.draw(surface)
        bf.Context.current_scene = None
        bf.Context.current_camera = None
        if self.current_transition is not None:
            self.current_transition[1].set_source(surface)
            tmp = surface.copy()
            self.get_scene(self.current_transition[0]).draw(tmp)
            self.current_transition[1].set_dest(tmp)
            self.current_transition[1].draw(surface)

from __future__ import annotations
import pygame
import batFramework as bf


class Scene:
    def __init__(self, name, enable_alpha=True) -> None:
        self._name = name
        self._active = False
        self._visible = False
        self._world_entities: list[bf.Entity] = []
        self._hud_entities: list[bf.Entity] = []
        self.manager: bf.SceneManager = None
        self._action_container: bf.ActionContainer = bf.ActionContainer()
        self.camera: bf.Camera = bf.Camera()
        self.hud_camera: bf.Camera = bf.Camera()
        if enable_alpha:
            self.camera.surface = self.camera.surface.convert_alpha()
            self.hud_camera.surface = self.camera.surface.convert_alpha()

            self.camera.set_clear_color((0, 0, 0))
            self.hud_camera.set_clear_color((0, 0, 0, 0))

        self.blit_calls = 0

    def set_sharedVar(self, name, value):
        return self.manager.set_sharedVar(name, value)

    def get_sharedVar(self, name):
        return self.manager.get_sharedVar(name)

    def do_when_added(self):
        pass

    def set_clear_color(self, color: pygame.Color):
        self.camera.set_clear_color(color)
        # self.hud_camera.set_clear_color(color)

    def set_manager(self, manager_link: bf.SceneManager):
        self.manager = manager_link

    def set_visible(self, value: bool):
        self._visible = value
        self.manager.update_scene_states()

    def set_active(self, value):
        self._active = value
        self.manager.update_scene_states()

    def is_active(self) -> bool:
        return self._active

    def is_visible(self) -> bool:
        return self._visible

    def get_name(self) -> str:
        return self._name

    def add_world_entity(self, *entity: bf.Entity):
        for e in entity:
            if e not in self._world_entities:
                self._world_entities.append(e)
                e.parent_scene = self
                e.do_when_added()

    def remove_world_entity(self, *entity: bf.Entity):
        # print("removing ",entity)
        for e in entity:
            if e not in self._world_entities:
                return False
            e.do_when_removed()
            e.parent_scene = None
            self._world_entities.remove(e)
            return True

    def add_hud_entity(self, *entity: bf.Entity):
        for e in entity:
            if e not in self._hud_entities:
                self._hud_entities.append(e)
                e.parent_scene = self
                e.do_when_added()

    def remove_hud_entity(self, *entity: bf.Entity):
        for e in entity:
            if e in self._hud_entities:
                e.do_when_removed()
                e.parent_scene = None
                self._hud_entities.remove(e)

    def add_action(self, *action):
        self._action_container.add_action(*action)

    def get_by_tags(self, *tags):
        return [
            entity
            for entity in self._world_entities + self._hud_entities
            if any(entity.has_tag(t) for t in tags)
        ]

    def get_by_uid(self, uid) -> bf.Entity | None:
        return next(
            (
                entity
                for entity in self._world_entities + self._hud_entities
                if entity.uid == uid
            ),
            None,
        )

    # called before process event
    def do_early_process_event(self, event: pygame.Event) -> bool:
        """return True if stop event propagation in child entities and scene's action container"""
        return False

    # propagates event to all entities
    def process_event(self, event: pygame.Event):
        """
        Propagates event to child events. Calls early process event first, if returns False then stops. Processes scene's action_container, then custom do_handle_event function.
        Finally resets the action_container, and propagates to all child entities. if any of them returns True, the propagation is stopped.
        """
        if self.get_sharedVar("in_transition"):
            return
        if self.do_early_process_event(event):
            return
        self._action_container.process_event(event)
        self.do_handle_event(event)
        self._action_container.reset()
        for entity in self._world_entities + self._hud_entities:
            if entity.process_event(event):
                return

    def do_handle_event(self, event: pygame.Event):
        """called inside process_event but before resetting the scene's action container and propagating event to child entities of the scene"""
        pass

    def update(self, dt):
        for entity in self._world_entities + self._hud_entities:
            entity.update(dt)
        self.do_update(dt)
        self.camera.update(dt)
        self.hud_camera.update(dt)

    def do_update(self, dt):
        pass

    def debug_entity(self, entity: bf.Entity, camera: bf.Camera):
        # return
        if not entity.visible:
            return
        for r in entity.get_bounding_box():
            pygame.draw.rect(
                camera.surface, entity._debug_color, camera.transpose(r), 1
            )

    def draw(self, surface: pygame.Surface):
        self._world_entities.sort(key=lambda e: e.render_order)
        self._hud_entities.sort(key=lambda e: e.render_order)

        total_blit_calls = 0
        self.camera.clear()
        self.hud_camera.clear()

        self.do_early_draw(self.camera.surface)

        total_blit_calls += sum(
            entity.draw(self.camera) for entity in self._world_entities
        )
        if self.manager._debugging == 2:
            for entity in self._world_entities:
                self.debug_entity(entity, self.camera)
        self.do_post_world_draw(self.camera.surface)

        total_blit_calls += sum(
            entity.draw(self.hud_camera) for entity in self._hud_entities
        )
        if self.manager._debugging == 2:
            for entity in self._hud_entities:
                self.debug_entity(entity, self.hud_camera)
        self.do_final_draw(self.hud_camera.surface)

        self.camera.draw(surface)
        self.hud_camera.draw(surface)

        self.blit_calls = total_blit_calls

    def do_early_draw(self, surface: pygame.Surface):
        pass

    def do_post_world_draw(self, surface: pygame.Surface):
        pass

    def do_final_draw(self, surface: pygame.Surface):
        pass

    def on_enter(self):
        pass

    def on_exit(self):
        pass

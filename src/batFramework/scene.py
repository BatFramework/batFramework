from __future__ import annotations
import re
from typing import TYPE_CHECKING,Any
if TYPE_CHECKING:
    from .manager import Manager
import pygame
import batFramework as bf


class Scene:
    def __init__(self, name, enable_alpha=True) -> None:
        self._name = name
        self._active = False
        self._visible = False
        self._world_entities: list[bf.Entity] = []
        self._hud_entities: list[bf.Entity] = []
        self.manager: Manager | None = None
        self.actions: bf.ActionContainer = bf.ActionContainer()
        self.camera: bf.Camera = bf.Camera()
        self.scene_index = 0
        self.hud_camera: bf.Camera = bf.Camera()
        if enable_alpha:
            self.camera.surface = self.camera.surface.convert_alpha()
            self.hud_camera.surface = self.camera.surface.convert_alpha()

            self.camera.set_clear_color((0, 0, 0))
            self.hud_camera.set_clear_color((0, 0, 0, 0))

        self.root  : bf.Root = bf.Root()
        self.root.set_center(*self.hud_camera.get_center())
        self.add_hud_entity(self.root)
        self.blit_calls = 0

    def set_scene_index(self,index):
        self.scene_index = index

    def get_scene_index(self):
        return self.scene_index

    def set_sharedVar(self, name, value)->bool:
        if not self.manager : return False 
        return self.manager.set_sharedVar(name, value)

    def get_sharedVar(self, name)->Any:
        if not self.manager : return False 
        return self.manager.get_sharedVar(name)

    def do_when_added(self):
        pass

    def set_clear_color(self, color: pygame.Color|tuple):
        self.camera.set_clear_color(color)
        # self.hud_camera.set_clear_color(color)

    def set_manager(self, manager_link: Manager):
        self.manager = manager_link

    def set_visible(self, value: bool):
        self._visible = value
        if self.manager : self.manager.update_scene_states()

    def set_active(self, value):
        self._active = value
        if self.manager : self.manager.update_scene_states()

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
        self.actions.add_action(*action)

    def get_by_tags(self, *tags):
        res =  [
            entity
            for entity in self._world_entities + self._hud_entities
            if any(entity.has_tag(t) for t in tags)
        ]
        res.extend(
            list(self.root.get_by_tags(*tags))
        )
        return res

    def get_by_uid(self, uid) -> bf.Entity | None:
        return next(
            (
                entity
                for entity in self._world_entities + self._hud_entities
                if entity.uid == uid
            ),
            None,
        )
        # TODO
        # ADD FOR WIDGETS TOO TOO

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
        self.actions.process_event(event)
        self.do_handle_actions()
        self.do_handle_event(event)
        for entity in self._world_entities + self._hud_entities:
            if entity.process_event(event):
                break
        
        self.actions.reset()

    def do_handle_actions(self)->None:
        pass

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
        # print(entity,entity.visible)
        for data in entity.get_bounding_box():
            if isinstance(data,pygame.FRect):
                rect = data
                color = entity._debug_color
            else:
                rect = data[0]
                color = data[1]
            if not isinstance(color,pygame.Color): color = pygame.Color(color)

            pygame.draw.rect(camera.surface, color , camera.transpose(rect), 1)

    def draw(self, surface: pygame.Surface):
        self._world_entities.sort(key=lambda e: (e.z_depth, e.render_order))
        self._hud_entities.sort(key=lambda e: (e.z_depth, e.render_order))

        total_blit_calls = 0
        self.camera.clear()
        self.hud_camera.clear()

        debug_2_or_3 = self.manager and self.manager._debugging in [2, 3]
        debug_3 = debug_2_or_3 and self.manager._debugging == 3

        total_blit_calls += sum(
            entity.draw(self.camera) for entity in self._world_entities
            if not (debug_2_or_3 and ((debug_3 and not entity.visible) or not debug_3))
        )

        if debug_2_or_3:
            for entity in self._world_entities:
                if debug_3 and not entity.visible:
                    continue
                self.debug_entity(entity, self.camera)

        total_blit_calls += sum(
            entity.draw(self.hud_camera) for entity in self._hud_entities
            if not (debug_2_or_3 and ((debug_3 and not entity.visible) or not debug_3))
        )

        if debug_2_or_3:
            for entity in self._hud_entities:
                if debug_3 and not entity.visible:
                    continue
                self.debug_entity(entity, self.hud_camera)


        self.do_early_draw(surface)
        self.camera.draw(surface)
        self.do_post_world_draw(surface)
        self.hud_camera.draw(surface)
        self.do_final_draw(surface)

        self.blit_calls = total_blit_calls

    def do_early_draw(self, surface: pygame.Surface):
        pass

    def do_post_world_draw(self, surface: pygame.Surface):
        pass

    def do_final_draw(self, surface: pygame.Surface):
        pass

    def on_enter(self):
        self.set_active(True)
        self.set_visible(True)
        self.root.build()


    def on_exit(self):
        self.root.focus_on(None)
        self.root.hover = None
        self.set_active(False)
        self.set_visible(False)
        self.actions.hard_reset()

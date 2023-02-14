from typing import TYPE_CHECKING

import pygame
from pygame.math import Vector2
from .camera import Camera
from .entitiy import Entity

if TYPE_CHECKING:
    from scene_manager import SceneManager
    from game_manager import GameManager


class Scene:
    def __init__(self, gameManagerLink : "GameManager", sceneManagerLink: "SceneManager"):
        self._gameManagerLink : GameManager = gameManagerLink
        self._sceneManagerLink: SceneManager = sceneManagerLink
        self._entities: pygame.sprite.OrderedUpdates = pygame.sprite.OrderedUpdates()
        self._id: str = ""
        self._is_active = True
        self._is_visible = True
        self._gravity = 10
        self._camera = Camera(pygame.display.get_surface().get_size())
        self.on_init()

    def set_id(self, name: str):
        self._id = name

    def get_id(self) -> str:
        return self._id

    def set_gravity(self, value: float):
        self._gravity = value

    def get_gravity(self) -> float:
        return self._gravity

    def get_world_coordinates(self, x, y)->Vector2:
        return Vector2(x,y)/ self._camera.get_zoom() + self._camera.get_position()

    def get_screen_coordinates(self, x, y)->Vector2:
        return Vector2(x,y) / self._camera.get_zoom() - self._camera.get_position()

    def get_mouse_world_coordinates(self)->Vector2:
        return self.get_world_coordinates(*pygame.mouse.get_pos())

    def set_game_manager_link(self, managerLink):
        self._gameManagerLink = managerLink

    def set_scene_manager_link(self, sceneManagerLink):
        self._sceneManagerLink = sceneManagerLink

    def get_game_manager(self):
        return self._gameManagerLink

    def get_scene_manager(self):
        return self._sceneManagerLink

    def on_init(self):
        pass

    def is_active(self) -> bool:
        return self._is_active

    # is drawn when visible
    def is_visible(self) -> bool:
        return self._is_visible

    def set_active(self, value: bool):
        self._is_active = value

    def set_visible(self, value: bool):
        self._is_visible = value

    def on_enter(self):
        pass

    def on_exit(self):
        self.set_active(False)
        self.set_visible(False)

    # not to override
    def _on_key_down(self, key):
        if key == pygame.K_d and pygame.key.get_mods() & pygame.KMOD_CTRL:
            self._camera.toggle_debug()
        for entity in self._entities:
            if entity.on_key_down(key):
                break
        self.on_key_down(key)

    def _on_key_up(self, key):
        for entity in self._entities:
            if entity.on_key_up(key):
                break
        self.on_key_up(key)

    def _on_event(self, event: pygame.event.Event):
        for entity in self._entities:
            if entity.on_event(event)== True:
                break
        self.on_event(event)

    # to override
    def on_key_down(self, key):
        pass

    def on_key_up(self, key):
        pass

    def on_event(self, event: pygame.event.Event):
        pass

    def add_entity(self, entity: Entity):
        self._entities.add(entity)
        entity.set_scene_manager_link(self.get_scene_manager())
        entity.set_scene_link(self)

    def clear_entities(self):
        self._entities.empty()

    def _update(self, dt: float):
        colliders = sum(
            [e.get_collider() for e in self._entities if e.is_collider()], []
        )
        dynamicEntites = [
            e for e in self._entities if e.has_collision() or e.is_gravity_affected()
        ]

        for entity in dynamicEntites:
            if entity.is_gravity_affected():
                entity.add_velocity(0, self.get_gravity() * dt)
            entity.apply_velocity_y(dt)
            if entity.has_collision():
                for collider in colliders:
                    if entity.rect.colliderect(collider):
                        entity.on_collision_y(collider)
                        break

            entity.apply_velocity_x(dt)
            if entity.has_collision():
                for collider in colliders:
                    if entity.rect.colliderect(collider):
                        entity.on_collision_x(collider)
                        break

        self._entities.update(dt)

        self._camera.update(dt)
        self.update(dt)

    def update(self, dt: float):
        pass

    def draw(self, surface: pygame.Surface):
        self._camera.clear()
        for entity in self._entities:
            entity.draw(self._camera)  # draw everything onto the camera surf
        self._camera.draw(surface)  # update surf with the camera

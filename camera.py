import pygame
from pygame.math import Vector2

from batFramework import Color
from batFramework.entitiy import Entity
from batFramework.render_surface import RenderSurface


class Camera:
    def __init__(self, resolution) -> None:
        self._position = Vector2(0, 0)
        self._zoom = 1
        self._baseResolution = resolution
        self._targetEntity: pygame.sprite.Sprite = None
        self._renderSurface = RenderSurface(resolution)
        self._scaledSurface = None
        self.centerPoint = Vector2(self.get_surface().get_rect().center)
        self._debug = False
        self._clearColor = Color.BLACK
        self.drawList = []
        self.hudDrawList = []
        self.rectDrawList = []
        self.secondRectDrawList = []

    def set_debug(self, value: bool):
        self._debug = value

    def toggle_debug(self):
        self.set_debug(not self._debug)

    def clear(self):
        self.get_surface().fill(self._clearColor)

    def set_clear_color(self, color: list[int]):
        self._clearColor = color

    def get_render_surface(self) -> RenderSurface:
        return self._renderSurface

    def get_surface(self):
        return self._renderSurface.get_surface()

    def get_surface_rect(self):
        return self.get_surface().get_rect()

    def unfollow_entity(self):
        self._targetEntity = None

    def follow_entity(self, entity: pygame.sprite.Sprite):
        self._targetEntity = entity

    def set_position(self, newPosition: list[int]):
        self._position.update(newPosition)
        self.centerPoint.update(self.get_surface_rect().move(self._position).center)

    def set_center(self, newPosition):
        self.centerPoint.update(newPosition)
        self._position.update(self.get_boundary().topleft)

    def get_position(self):
        return self._position

    def set_zoom(self, value: float):
        if value < 0.4 or value > 3:
            print("Bad zoom value : ", value)
            return
        if value != self._zoom:
            self._zoom = value
            self._renderSurface.set_zoom(value)
            print(self.get_surface().get_size())
            #self.set_center(self.centerPoint)

    def get_zoom(self) -> float:
        return self._zoom

    def get_boundary(self):
        r = pygame.rect.Rect(0, 0, *[(i / self._zoom) for i in self._baseResolution])
        r.center = self.centerPoint
        return r

    def is_rect_visible(self, rect: pygame.rect.Rect):
        return self.get_boundary().colliderect(rect)

    def update(self, dt: float):
        if self._targetEntity:
            self.set_center(self._targetEntity.rect.center)

    def blit_entity(self, entity: Entity, special_flags: int = 0):
        if (not entity._is_hud) and not self.is_rect_visible(entity.rect):
            return
        if entity._is_hud:
            self.hudDrawList.append((entity.image, entity.rect.copy(), None, special_flags))

        else:
            self.drawList.append(
                (
                    entity.image,
                    entity.rect.move(*-self.get_position()),
                    None,
                    special_flags,
                )
            )

        if not self._debug:
            return
        self.draw_rect(Color.RED, entity.rect, 1, -1, entity._is_hud,entity._is_hud)

    def blit(
        self, surface: pygame.surface.Surface, dest, special_flags: int = 0, hud=False
    ):
        if not self.is_rect_visible(surface.get_rect().move(dest)):
            return
        if hud:
            self.hudDrawList.append(
                (surface, dest - self.get_position(), None, special_flags)
            )

        else:
            self.drawList.append(
                (surface, dest - self.get_position(), None, special_flags)
            )

    def draw_rect(
        self, color, rect, width=0, borderRadius=-1, hud=False, afterEntities=False
    ):
        if not self.is_rect_visible(rect):return
        if not afterEntities:
            self.rectDrawList.append(
                [
                    color,
                    rect.move(-self._position) if not hud else rect,
                    width,
                    borderRadius,
                ]
            )
        else:
            self.secondRectDrawList.append(
                [
                    color,
                    rect.move(-self._position) if not hud else rect,
                    width,
                    borderRadius,
                ]
            )

    def blit_rects(self, surface):
        for data in self.rectDrawList:
            pygame.draw.rect(surface, *data)
        self.rectDrawList = []

    def blit_second_rects(self, surface):
        for data in self.secondRectDrawList:
            pygame.draw.rect(surface, *data)
        self.secondRectDrawList = []

    def draw(self, surface: pygame.surface.Surface):
        self.get_surface().blits(self.drawList)
        self.blit_rects(self.get_surface())



        if self._zoom == 1:
            self.get_surface().blits(self.hudDrawList)
            self.blit_second_rects(self.get_surface())
            surface.blit(self.get_surface(), (0, 0))
            self.drawList = []
            self.hudDrawList = []
            return
        
        rect = pygame.Rect(0, 0, *self.get_boundary().size)
        rect.center = self.get_surface_rect().center
        sub = self.get_surface().subsurface(rect)
        pygame.transform.scale(sub, surface.get_size(), surface)
        surface.blits(self.hudDrawList)
        self.blit_second_rects(surface)
        self.drawList = []
        self.hudDrawList = []

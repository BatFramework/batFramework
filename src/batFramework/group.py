from __future__ import annotations
import logging
import pygame
import batFramework as bf
from typing import Iterator, Self

logger = logging.getLogger(__name__)


class Group(bf.Drawable):
    """
    Groups drawables into a single entity of the scene.

    The scene only sees the group. The group owns its members, relays the
    entity hooks to them (update, process_event, parent scene changes, ...)
    and draws them sorted by draw_order, so a group isolates the ordering of
    its members from the rest of the scene. Members use the group's layer.

    Batching (on by default): each run of consecutive members that use the
    default Drawable.draw is drawn with fblits. Members with a custom draw
    method (particles, scrolling sprites, widgets, nested groups...) are drawn
    with it, between the batches around them.

    blit_flags: None (default) keeps each member's own blit flags, a value
    overrides them for every batched member.

    Membership changes are applied at the end of the group's update (or when
    the group joins/leaves a scene), like scene.add / scene.remove.
    The draw list is rebuilt at that point.
    """

    def __init__(
        self,
        *entities: bf.Drawable,
        blit_flags: int | None = None,
        batching: bool = True,
    ) -> None:
        super().__init__((0, 0))
        self.entities: list[bf.Drawable] = []
        self._members: set[bf.Drawable] = set()
        self._to_add: list[bf.Drawable] = []
        self._to_remove: list[bf.Drawable] = []
        self._should_reorder: bool = False
        # runs of batchable members (lists) and individually drawn members, in draw order
        self._draw_list: list[list[bf.Drawable] | bf.Drawable] = []
        self.blit_flags: int | None = blit_flags
        self.batching: bool = batching
        self.set_debug_color("white")
        self.add(*entities)

    def set_blit_flags(self, blit_flags: int | None) -> Self:
        """None keeps each member's own flags, a value overrides them for batched members"""
        self.blit_flags = blit_flags
        return self

    def set_batching(self, value: bool) -> Self:
        if value != self.batching:
            self.batching = value
            self._build_draw_list()
        return self

    # ------------------------------------------------------------------
    # Membership
    # ------------------------------------------------------------------

    def add(self, *entities: bf.Drawable) -> Self:
        for e in entities:
            if e._parent_group is self or e is self:
                continue
            if e._parent_group is not None:
                e._parent_group.remove(e)
            elif e.parent_scene is not None:
                logger.warning(
                    f"{e} is already in {e.parent_scene}, remove it from the scene before adding it to a Group"
                )
            e._parent_group = self
            self._to_add.append(e)
        return self

    def remove(self, *entities: bf.Drawable) -> Self:
        for e in entities:
            if e._parent_group is not self:
                continue
            e._parent_group = None
            self._to_remove.append(e)
        return self

    def clear(self) -> Self:
        return self.remove(*self.entities, *self._to_add)

    def __iter__(self) -> Iterator[bf.Drawable]:
        # stale entries (removed or moved to another group) are skipped until the next flush
        return (e for e in self.entities if e._parent_group is self)

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __bool__(self) -> bool:
        # a group is an entity: stay truthy when empty (e.g. `if entity.parent_group:`)
        return True

    def __contains__(self, entity: bf.Drawable) -> bool:
        return entity._parent_group is self

    def get_by_tags(self, *tags) -> bf.Drawable | None:
        for e in self:
            if e.has_tags(*tags):
                return e
        return None

    def get_all_by_tags(self, *tags) -> list[bf.Drawable]:
        return [e for e in self if e.has_tags(*tags)]

    def request_draw_order_update(self) -> None:
        self._should_reorder = True

    def flush_entity_changes(self) -> None:
        changed = self._should_reorder or bool(self._to_remove or self._to_add)
        if self._to_remove:
            for e in self._to_remove:
                # if it was moved to another group, that group handles its scene
                if e._parent_group is None and e in self._members:
                    e.set_parent_scene(None)
            self._to_remove.clear()
            self.entities = [e for e in self.entities if e._parent_group is self]
            self._members = set(self.entities)

        if self._to_add:
            for e in self._to_add:
                if e._parent_group is not self or e in self._members:
                    continue
                self.entities.append(e)
                self._members.add(e)
                e.set_parent_scene(self.parent_scene)
            self._to_add.clear()
            self._should_reorder = True

        if self._should_reorder:
            self.entities.sort(key=lambda e: e.draw_order)
            self._should_reorder = False

        if changed:
            self._build_draw_list()

    # ------------------------------------------------------------------
    # Relayed hooks
    # ------------------------------------------------------------------

    def set_parent_scene(self, scene) -> Self:
        if scene == self.parent_scene:
            return self
        super().set_parent_scene(scene)
        self.flush_entity_changes()
        for e in self:
            e.set_parent_scene(scene)
        return self

    def process_event(self, event: pygame.Event) -> None:
        if event.consumed:
            return
        # top-most first, like the scene
        for e in reversed(self.entities):
            if e._parent_group is not self:
                continue
            e.process_event(event)
            if event.consumed:
                return
        super().process_event(event)

    def update(self, dt: float) -> None:
        for e in self:
            e.update(dt)
        self.flush_entity_changes()
        super().update(dt)

    def get_debug_outlines(self):
        if not self.visible:
            return
        for e in self:
            yield from e.get_debug_outlines()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _build_draw_list(self) -> None:
        self._draw_list = []
        if not self.batching:
            self._draw_list.extend(self.entities)
            return
        run: list[bf.Drawable] = []
        for e in self.entities:
            if type(e).draw is bf.Drawable.draw:
                run.append(e)
                continue
            if run:
                self._draw_list.append(run)
                run = []
            self._draw_list.append(e)
        if run:
            self._draw_list.append(run)

    def get_blit_data(self, camera: bf.Camera):
        return None

    def draw(self, camera: bf.Camera) -> None:
        if not self.visible:
            return
        fblits = camera.surface.fblits
        override = self.blit_flags
        for item in self._draw_list:
            if not isinstance(item, list):
                item.draw(camera)
            elif override is not None:
                fblits(
                    [d for e in item if (d := e.get_blit_data(camera)) is not None],
                    override,
                )
            else:
                # split the run wherever the members' own flags change
                batch = []
                flags = 0
                for e in item:
                    data = e.get_blit_data(camera)
                    if data is None:
                        continue
                    if e.blit_flags != flags and batch:
                        fblits(batch, flags)
                        batch = []
                    flags = e.blit_flags
                    batch.append(data)
                if batch:
                    fblits(batch, flags)

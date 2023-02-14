
import pygame

from .anchor import Anchor
from .camera import Camera
from .color import Color
from .entitiy import Entity
from .interactive_entity import InteractiveEntity


class GuiContainer(InteractiveEntity):
    def __init__(self) -> None:
        super().__init__()
        self._entities: list[Entity] = []
        self._interactiveEntities: list[InteractiveEntity] = []
        self._direction = "vertical"
        self._layout = "fit"
        self._color = Color.BLACK
        self._gap = 0
        self._itemIndex = 0
        self._padding = [0, 0]
        self._focusPadding = [0, 0]
        self._borderRadius = -1
        self._focusBorderRadius = -1
        self._focusColor = Color.WHITE
        self._alignement: Anchor = Anchor.LEFT
        self._showFocus = True

    def set_visible(self, val: bool):
        super().set_visible(val)
        for entity in self._entities:
            entity.set_visible(val)

    def set_scene_link(self, sceneLink):
        super().set_scene_link(sceneLink)
        for entity in self._entities:
            sceneLink.add_entity(entity)

    def set_hud(self, value: bool):
        super().set_hud(value)
        for entity in self._entities:
            entity.set_hud(value)

    def set_focus_color(self, color: tuple[int]):
        self._focusColor = color

    def set_show_focus(self, value: bool):
        self._showFocus = value

    def switch_container(self, new: "GuiContainer", show=False):
        new.set_visible(True)
        self.set_visible(show)
        self.lose_focus()
        new.get_focus()

    def set_focus_border_radius(self, value):
        self._focusBorderRadius = value

    def set_focus_padding(self, x: int, y: int):
        if x < 0 or y < 0:
            return
        self._focusPadding = [x, y]

    def set_position(self, x, y):
        super().set_position(x, y)
        self.update_position()

    def set_border_radius(self, value):
        self._borderRadius = value


        if isinstance(value, list):
            if all([x <= 0 for x in value]):
                self.image.fill(self.get_color())
                return
            self.image.fill(Color.TRANSPARENT)

            pygame.draw.rect(
                self.image, self.get_color(), self.image.get_rect(), 0, *value
            )

        elif isinstance(value, int):
            if value <= 0:
                self.image.fill(self.get_color())
                return
            self.image.fill(Color.TRANSPARENT)
            pygame.draw.rect(
                self.image, self.get_color(), self.image.get_rect(), 0, value
            )

    def set_alignement(self, anchor: Anchor):
        if anchor not in [
            Anchor.UP,
            Anchor.DOWN,
            Anchor.LEFT,
            Anchor.RIGHT,
            Anchor.CENTER,
        ]:
            print("Anchor not supported :(", anchor)
            return False
        self._alignement = anchor
        for entity in self._entities:
            match anchor:
                case Anchor.UP | Anchor.LEFT:
                    entity.set_anchor(Anchor.TOPLEFT)
                case Anchor.RIGHT:
                    entity.set_anchor(Anchor.TOPRIGHT)
                case _:
                    entity.set_anchor(Anchor.CENTER)
        self.update_position()
        return True

    def set_layout(self, layout: str):
        if layout not in ["fit", "fill", "fixed"]:
            return False
        self._layout = layout
        self.update_dimensions()

    def set_direction(self, direction: str):
        aliases = {"h": "horizontal", "v": "vertical"}
        if direction in aliases:
            direction = aliases[direction]
        if direction in ["vertical", "horizontal"]:
            self._direction = direction
            self.update_dimensions()
            return True
        return False

    def is_empty(self) -> bool:
        return len(self._entities) == 0

    def set_color(self, color: list[int]):
        self._color = color
        self.set_border_radius(self._borderRadius)

    def get_color(self) -> list[int]:
        return self._color

    def set_gap(self, value: int):
        if value < 0:
            return
        self._gap = value
        self.update_dimensions()

    def set_padding(self, x: int, y: int):
        if x < 0 or y < 0:
            return
        self._padding = [x, y]
        self.update_dimensions()

    def get_focus(self):
        super().get_focus()
        if self.is_empty() or len(self._interactiveEntities) == 0:
            return
        print(self._interactiveEntities,self._itemIndex)
        self._interactiveEntities[self._itemIndex].get_focus()

    def lose_focus(self):
        super().lose_focus()
        if not self.is_empty():
            self._interactiveEntities[self._itemIndex].lose_focus()

    def has_focus(self) -> bool:
        return self._has_focus

    def set_focus_index(self, index: int):
        if self._itemIndex == index : return
        if self.is_empty() or index < 0 or index >= len(self._interactiveEntities):
            return False
        self._interactiveEntities[self._itemIndex].lose_focus()
        self._itemIndex = index
        self._interactiveEntities[self._itemIndex].get_focus()

    def get_focus_index(self) -> int:
        return self._itemIndex

    def get_focused_item(self) -> InteractiveEntity:
        if self.is_empty() or len(self._interactiveEntities) == 0:
            return None
        return self._interactiveEntities[self._itemIndex]

    def get_entity_focus_index(self,entity: InteractiveEntity)->int:
        if not entity in self._interactiveEntities:
            return -1
        return self._interactiveEntities.index(entity)

    def update_position(self):
        if self.is_empty():
            return
        tmp = 0
        if self._direction == "vertical":
            tmp = self.rect.top + self._padding[1]
            for entity in self._entities:
                match self._alignement:
                    case Anchor.LEFT:
                        entity.set_position(self.rect.left + self._padding[0], tmp)
                    case Anchor.CENTER:
                        entity.set_position(
                            self.rect.centerx, tmp + entity.get_size()[1] // 2
                        )
                    case Anchor.RIGHT:
                        entity.set_position(self.rect.right - self._padding[0], tmp)
                    case _:
                        print("unsupported alignement : ", self._alignement)

                tmp += entity.rect.height + self._gap

        elif self._direction == "horizontal":
            tmp = self.rect.x + self._padding[0]
            for entity in self._entities:
                match self._alignement:
                    case Anchor.UP:
                        entity.set_position(tmp, self.rect.top + self._padding[1])

                    case Anchor.CENTER:
                        entity.set_position(
                            tmp + entity.get_size()[0] // 2, self.rect.centery
                        )

                    case Anchor.DOWN:
                        entity.set_position(tmp, self.rect.bottom - self._padding[1])
                    case _:
                        print("unsupported alignement : ", self._alignement)

                tmp += entity.rect.width + self._gap

    def update_dimensions(self):
        if self.is_empty():
            return
        if self._direction == "vertical":
            match self._layout:
                case "fit":
                    widest = max([entity.rect.width for entity in self._entities])
                    width = widest + self._padding[0] * 2
                    totalHeight = sum(
                        [entity.rect.height + self._gap for entity in self._entities]
                    )
                    totalHeight -= self._gap
                    height = totalHeight + (self._padding[1] * 2)
                    self.set_size(width, height)
                    
                case "fill":
                    for entity in self._entities:
                        if entity.isSizeLocked():
                            continue
                        entity.set_size(
                            self.rect.width - (self._padding[0] * 2),
                            entity.get_rect().height,
                        )


        elif self._direction == "horizontal":
            match self._layout:
                case "fit":
                    width = (
                        sum([entity.rect.width for entity in self._entities])
                        + self._padding[0] * 2
                        - self._gap
                    )
                    height = max(
                        [entity.rect.height + self._gap for entity in self._entities]
                    ) + (self._padding[1] * 2)
                    self.set_size(width, height)

        self.set_position(*self.get_position())
        self.image = pygame.Surface(self.rect.size).convert_alpha()
        self.set_color(self.get_color())

    def add_interactive(self, entity: InteractiveEntity) ->int:
        self._interactiveEntities.append(entity)
        self.add(entity)
    
    def add(self, entity: Entity):
        self._entities.append(entity)
        entity.set_parent_container(self)
        entity.set_hud(self.is_hud())
        entity.set_visible(self.is_visible())
        self.set_alignement(self._alignement)
        self.update_dimensions()
        if self.get_scene_link():self.get_scene_link().add_entity(entity)

    def remove(self, entity: Entity):
        if entity in self._interactiveEntities:
            self._interactiveEntities.remove(entity)
        self._entities.remove(entity)
        self.update_dimensions()



    def on_key_down(self, key):
        if not self.has_focus():
            return False
        if key == pygame.K_DOWN:
            if self.set_focus_index(self.get_focus_index() + 1) == False:
                self.set_focus_index(0)
        elif key == pygame.K_UP:
            if self.set_focus_index(self.get_focus_index() - 1) == False:
                self.set_focus_index(len(self._interactiveEntities) - 1)
        else:
            self.get_focused_item().on_key_down(key)
            return True
        return False

    def draw(self, camera: Camera):
        if not self.is_visible():
            return
        if not self.is_hud() and  not camera.is_rect_visible(self.rect): return
        super().draw(camera)
        if self.has_focus() and len(self._interactiveEntities) > 0:
            camera.draw_rect(
                self._focusColor,
                self.get_focused_item().rect.inflate(*self._focusPadding),
                3,
                self._focusBorderRadius,
                self.is_hud(),
                True,
            )

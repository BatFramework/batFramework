import batFramework as bf
import pygame
from .panel import Panel
from .interactiveEntity import InteractiveEntity


class Container(Panel, InteractiveEntity):
    def __init__(self, uid=None, layout: bf.Layout = bf.Layout.FILL):
        bf.Panel.__init__(self)
        InteractiveEntity.__init__(self)
        if uid:
            self.set_uid(uid)
        self._background_color = None  # bf.const.DARK_INDIGO
        self._border_radius = [0]
        self._padding = (0, 0)

        self.children: list[bf.Panel] = []
        self.interactive_children: list[InteractiveEntity] = []

        self.focused_index = 0
        self._no_focusable_child = True

        self.direction = bf.Direction.VERTICAL
        self.alignment = bf.Alignment.CENTER
        self.layout = layout
        self.gap = 4
        self.lock_focus = False
        self.switch_focus_sfx = None
        self._sfx_volume = 0.5

        self.actions = bf.ActionContainer(
            bf.Action("up").add_key_control(pygame.K_UP),
            bf.Action("down").add_key_control(pygame.K_DOWN),
            bf.Action("left").add_key_control(pygame.K_LEFT),
            bf.Action("right").add_key_control(pygame.K_RIGHT),
            bf.Action("tab").add_key_control(pygame.K_TAB),
        )

        self.set_debug_color(bf.color.BROWN)

    @staticmethod
    def create_link(
        source: "Container", dest: "Container", hide_source=False, reset_dest_focus=True
    ):
        def fun():
            source.lose_focus()
            if hide_source:
                source.set_visible(False)
            if reset_dest_focus:
                dest.set_focused_child_index(0)
            dest.set_visible(True)
            dest.get_focus()

        return fun

    def get_bounding_box(self):
        for child in self.children:
            for rect in child.get_bounding_box():
                yield rect
        yield self.rect
        yield self.rect.inflate(-self._padding[0] * 2, -self._padding[1] * 2)

    # def set_background_color(self,color):
    #     self._background_color = color
    #     self.update_surface()
    #     return self

    def set_padding(self, value: tuple[int]):
        self._padding = value
        self.update_content()
        return self

    def set_border_radius(self, value: int | list[int]):
        super().set_border_radius(value)
        self.update_content()
        return self

    def set_visible(self, value):
        super().set_visible(value)
        for child in set(self.children + self.interactive_children):
            child.set_visible(value)
        return self

    def set_position(self, x, y):
        if (x, y) == self.rect.topleft:
            return self
        dx, dy = x - self.rect.left, y - self.rect.top
        super().set_position(x, y)
        for child in self.children:
            child.set_position(*child.rect.move(dx, dy).topleft)
        return self

    def set_center(self, x, y):
        if (x, y) == self.rect.center:
            return self
        dx, dy = x - self.rect.centerx, y - self.rect.centery
        super().set_center(x, y)
        for child in self.children:
            child.set_position(*child.rect.move(dx, dy).topleft)
        return self

    def set_gap(self, value):
        self.gap = value
        self.update_content()
        return self

    def set_layout(self, layout: bf.Layout):
        """
        Set the layout mode of the container.

        Parameters:
            layout (Layout): The layout mode to set. Either Layout.FILL or Layout.FIT.
        """
        if layout in bf.Layout.__members__.values():
            self.layout = layout
        else:
            print(f"Invalid layout mode '{layout}'. Using default: {self.layout.name}")
        self.update_content()
        return self

    def set_direction(self, direction: bf.Direction):
        """
        Set the direction of the container.

        Parameters:
            direction (Direction): The direction to set. Either Direction.HORIZONTAL or Direction.VERTICAL.
        """
        if direction in bf.Direction.__members__.values():
            self.direction = direction
        else:
            print(
                f"Invalid direction '{direction}'. Using default: {self.direction.name}"
            )
        self.update_content()
        return self

    def set_alignment(self, alignment: bf.Alignment):
        """
        Set the direction of the container.

        Parameters:
            direction (Direction): The direction to set. Either Direction.HORIZONTAL or Direction.VERTICAL.
        """
        if alignment in bf.Alignment.__members__.values():
            self.alignment = alignment
        else:
            print(
                f"Invalid alignment '{alignment}'. Using default: {self.alignment.name}"
            )
        self.update_content()
        return self

    def add_entity(self, entity: bf.Entity):
        """
        Add an entity to the container.

        Parameters:
            entity (Entity): The entity to add.
        """
        self.children.append(entity)
        entity.set_parent_container(self)
        if isinstance(entity, InteractiveEntity):
            self.interactive_children.append(entity)
            self._no_focusable_child = False
        self.update_content()

    def remove_entity(self, entity: bf.Entity):
        """
        Remove an entity from the container.

        Parameters:
            entity (Entity): The entity to remove.
        """
        self.children.remove(entity)
        entity.set_parent_container(None)
        if isinstance(entity, InteractiveEntity):
            self.interactive_children.remove(entity)
            if len(self.interactive_children) == 0:
                self._no_focusable_child = True
        self.update_content()

    def get_focus(self):
        super().get_focus()
        try:
            self.get_focused_child().get_focus()
            return True
        except AttributeError:
            return False

    def lose_focus(self):
        super().lose_focus()
        # print(self.interactive_children,self._no_focusable_child,self.focused_index)
        try:
            self.get_focused_child().lose_focus()
            return True
        except AttributeError:
            return False

    def get_focused_child(self):
        if not self._focused or self._no_focusable_child:
            return None
        # print(self.focused_index,self.uid)
        return self.interactive_children[self.focused_index]

    def set_focused_child_index(self, index: int):
        if index < 0 or index >= len(self.interactive_children):
            return False
        self.interactive_children[self.focused_index].lose_focus()
        self.focused_index = index
        self.interactive_children[self.focused_index].get_focus()

    def set_focused_child(self, child: InteractiveEntity):
        try:
            index = self.interactive_children.index(child)
        except ValueError:
            return False
        if index != self.focused_index:
            self.set_focused_child_index(index)

    def next(self):
        self.set_focused_child_index( (self.focused_index + 1) % len(self.interactive_children))
        if self.switch_focus_sfx:
            bf.AudioManager().play_sound(self.switch_focus_sfx, self._sfx_volume)

    def prev(self):
        self.set_focused_child_index( (self.focused_index - 1) % len(self.interactive_children))
        if self.switch_focus_sfx:
            bf.AudioManager().play_sound(self.switch_focus_sfx, self._sfx_volume)

    def update(self, dt):
        for child in self.children:
            child.update(dt)

    def process_event(self, event):
        self.actions.process_event(event)
        if self._focused:
            if not self.lock_focus:
                if self.direction == bf.Direction.HORIZONTAL:
                    if self.actions.is_active("right") or self.actions.is_active("tab"):
                        self.next()
                    elif self.actions.is_active("left"):
                        self.prev()
                elif self.direction == bf.Direction.VERTICAL:
                    if self.actions.is_active("down") or self.actions.is_active("tab"):
                        self.next()
                    elif self.actions.is_active("up"):
                        self.prev()
            for child in self.children:
                child.process_event(event)
        self.actions.reset()

    def update_content(self):
        """
        Update the layout and positioning of the container's children.
        """
        if self.direction == bf.Direction.VERTICAL:
            self.update_vertical_layout()
        elif self.direction == bf.Direction.HORIZONTAL:
            self.update_horizontal_layout()
        # print(self.rect)
        if not self.surface or self.surface.get_size() != tuple(
            int(i) for i in self.rect.size
        ):
            self.surface = pygame.Surface(self.rect.size).convert_alpha()
            self.update_surface()

    def resize(self, new_width, new_height):
        self._manual_resized = True
        if (new_width, new_height) == self.rect.size:
            return
        # print(self.uid,new_width,new_height)
        bf.Panel.resize(self, new_width, new_height)
        self.update_content()

    def resize_by_parent(self, new_width, new_height):
        if self._manual_resized or (new_width, new_height) == self.rect.size:
            return
        bf.Panel.resize_by_parent(self, new_width, new_height)
        self.update_content()

    def resize_by_self(self, new_width, new_height):
        if (new_width, new_height) == self.rect.size:
            return self
        if self._set_position_center:
            tmp = self.rect.center
        self.rect.size = (new_width, new_height)
        if self._set_position_center:
            self.rect.center = tmp
        # self.update_surface()
        return self

    def update_vertical_layout(self):
        """
        Update the vertical layout and positioning of the container's children.
        """

        # height

        # _ = [c.update_surface() for c in self.children] if self.layout == bf.Layout.FIT else 0

        len_children = len(self.children)
        total_children_height = sum(child.rect.h for child in self.children)
        total_gap_height = max(0, (len_children - 1) * self.gap)
        total_height = max(
            0, total_children_height + total_gap_height + self._padding[1] * 2
        )

        max_child_width = (
            max(child.rect.w for child in self.children)
            if self.children
            else self.rect.w
        )

        if self._manual_resized:
            total_width, total_height = self.rect.size

        if self._parent_resize_request or self._manual_resized:
            total_height = max(0, self.rect.h)
            max_child_width = max(0, self.rect.w - self._padding[0] * 2)

        total_width = max_child_width + self._padding[0] * 2

        self.resize_by_self(total_width, total_height)

        self._update_vertical_children()

    def _update_vertical_children(self):
        max_child_width = self.rect.width - self._padding[0]*2
        
        start_y = self.rect.y + self._padding[1]

        for child in self.children:
            y = start_y
            x = self.rect.left
            if self.layout == bf.Layout.FILL:
                child.resize_by_parent(max_child_width, None)
            if self.alignment == bf.Alignment.LEFT:
                x = self.rect.x + self._padding[0]
            elif self.alignment == bf.Alignment.RIGHT:
                x = self.rect.right - child.rect.w - self._padding[0]
            elif self.alignment == bf.Alignment.CENTER:
                tmp = child.rect.copy()
                tmp.centerx = self.rect.centerx
                x = tmp.left
            child.set_position(x, y)
            start_y = child.rect.bottom + (self.gap if len(self.children) > 1 else 0)


    def update_horizontal_layout(self):
        """
        Update the horizontal layout and positioning of the container's children.
        """

        # Width
        len_children = len(self.children)
        total_children_width = sum(child.rect.w for child in self.children)
        total_gap_width = (len_children - 1) * self.gap
        total_width = max(
            0, total_children_width + total_gap_width + self._padding[0] * 2
        )

        max_child_height = (
            max(child.rect.h for child in self.children)
            if self.children
            else self.rect.h
        )

        if self._manual_resized:
            total_width, total_height = self.rect.size

        if self._parent_resize_request or self._manual_resized:
            total_width = max(0, self.rect.w)
            max_child_height = max(0, self.rect.h - self._padding[1] * 2)

        total_height = max_child_height + self._padding[1] * 2

        self.resize_by_self(total_width, total_height)

        start_x = self.rect.x + self._padding[0]

        for child in self.children:
            x = start_x
            y = self.rect.top
            if self.layout == bf.Layout.FILL:
                child.resize_by_parent(None, max_child_height)
            if self.alignment == bf.Alignment.TOP:
                y = self.rect.y + self._padding[1]
            elif self.alignment == bf.Alignment.BOTTOM:
                y = self.rect.bottom - child.rect.h - self._padding[1]
            elif self.alignment == bf.Alignment.CENTER:
                tmp = child.rect.copy()
                tmp.centery = self.rect.centery
                y = tmp.top
            child.set_position(x, y)
            start_x = child.rect.right + (self.gap if len_children > 1 else 0)

    def draw_focused_child(self, camera):
        child = self.get_focused_child()
        if child:
            child.draw_focused(camera)

    def draw(self, camera):
        """
        Draw the container and its children.

        Parameters:
            camera (Camera): The camera to draw the container onto.

        Returns:
            int: The number of entities drawn.
        """
        if not self.visible:
            return 0
        num_drawn = 1
        camera.surface.blit(self.surface, camera.transpose(self.rect))
        for child in [
            c
            for c in self.children
            if c.visible or not isinstance(c, InteractiveEntity) or not c._focused
        ]:
            child.draw(camera)
            num_drawn += 1
        if self._focused:
            self.draw_focused_child(camera)
            num_drawn += 1

        return num_drawn

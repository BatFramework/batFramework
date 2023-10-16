import pygame
import batFramework as bf


class Entity:
    def __init__(
        self,
        size : None|tuple[int,int]=None,
        no_surface : bool   =False,
        surface_flags : int =0,
        convert_alpha : bool=False
    ) -> None:
        self.convert_alpha = convert_alpha
        if size is None:
            size= (100,100)
            
        if no_surface:
            self.surface = None
        else:
            self.surface = (pygame.Surface(size, surface_flags))

        if convert_alpha and self.surface is not None:
            self.surface = self.surface.convert_alpha()
            self.surface.fill((0,0,0,0))

        self.uid: str | None= None
        self.tags: list[str] = []
        self.parent_scene: bf.Scene | None = None
        self.rect = pygame.FRect(0, 0, *size)
        
        self.visible = True
        self._debug_color = bf.color.DARK_RED
        self.render_order = 0
        self.z_depth = 1

    def get_bounding_box(self):
        yield self.rect

    def set_debug_color(self, color):
        self._debug_color = color

    def set_visible(self, value: bool):
        self.visible = value

    def set_parent_scene(self, scene):
        self.parent_scene = scene

    def do_when_added(self):
        pass

    def do_when_removed(self):
        pass

    def set_position(self, x, y):
        self.rect.topleft = (x, y)
        return self

    def set_x(self,x):
        self.rect.x = x
        return self

    def set_y(self,y):
        self.rect.y = y
        return self

    def set_center(self, x, y):
        self.rect.center = (x, y)
        return self

    def set_uid(self, uid):
        self.uid = uid
        return self

    def add_tag(self, *tags):
        for tag in tags:
            if tag not in self.tags:
                self.tags.append(tag)
        self.tags.sort()
        return self

    def remove_tag(self, *tags):
        self.tags = [tag for tag in self.tags if tag not in tags]
        self.tags.sort()

    def has_tag(self, tag) -> bool:
        return tag in self.tags

    def process_event(self, event: pygame.Event)->bool:
        # insert action process here
        self.do_handle_event(event)
        # insert action reset heres

        #return True if the method is blocking (no propagation to next children of the scene)
        return False
    def do_handle_event(self, event: pygame.Event):
        pass

    def update(self, dt: float):
        pass

    def draw(self, camera: bf.Camera) -> int:
        if not self.visible:
            return False
        if not self.surface or not camera.intersects(self.rect):
            return False
        camera.surface.blit(
            self.surface,
            tuple(round(i * self.z_depth) for i in camera.transpose(self.rect).topleft),
        )
        return True

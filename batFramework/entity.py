import pygame
import batFramework as bf
class Entity:
    # __slots__ = "surface","rect","velocity","uid","tags","parent_scene","visible","_debug_color","render_order","z_depth","parent_container"
    def __init__(self, size=None,no_surface = False,surface_flags = 0,convert_alpha =False) -> None:
        self.surface = pygame.Surface(size if size else (1,1),surface_flags) if no_surface == False else None
        if convert_alpha : self.surface = self.surface.convert_alpha()
        self.rect = pygame.FRect(0, 0, *size) if size else pygame.FRect(0, 0, 1, 1)
        self.velocity = pygame.math.Vector2(0,0)
        self.uid: str = None
        self.tags: list[str] = []
        self.parent_scene :bf.Scene = None
        self.visible = True
        self._debug_color = bf.color.DARK_RED
        self.render_order = 0
        self.z_depth = 1
        self.parent_container : "bf.Container" = None

    def set_parent_container(self,parent:"bf.Container"):
        self.parent_container = parent


    def get_bounding_box(self):
        yield self.rect

    def put_to(self,container:"bf.Container"):
        container.add_entity(self)
        return self

    def on_collideX(self,collider:"Entity"):
        pass

    def on_collideY(self,collider: "Entity"):
        pass
    
    def set_debug_color(self,color):
        self._debug_color = color
    

    def set_visible(self,value: bool):
        self.visible = value
    
    def set_parent_scene(self,scene):
        self.parent_scene = scene
    
    def do_when_added(self):
        pass
    
    def do_when_removed(self):
        pass
    
    def set_position(self, x, y):
        self.rect.topleft = (x, y)
        return self

    def set_center(self, x, y):
        self.rect.center = (x, y)
        return self

    def set_uid(self, uid):
        self.uid = uid
        return self

    def get_uid(self) -> str:
        return self.uid

    def add_tag(self, *tags):
        for tag in tags:
            if tag not in self.tags:
                self.tags.append(tag)
        self.tags.sort()
        return self
    def remove_tag(self,*tags):
        self.tags  = [tag for tag in self.tags if tag not in tags ]
        self.tags.sort()
    def has_tag(self, tag) -> bool:
        return tag in self.tags

    def process_event(self, event: pygame.Event):
        #insert action process here
        self.do_handle_event(event)
        #insert action reset heres

    def do_handle_event(self,event : pygame.Event):
        pass

    def update(self, dt: float):
        pass

    def draw(self, camera: bf.Camera) -> bool:
        if not self.visible : return False
        if not self.surface or not camera.intersects(self.rect): return False
        # pygame.draw.rect(camera.surface,"purple",camera.transpose(self.rect).move(2,2))
        camera.surface.blit(self.surface, tuple(round(i * self.z_depth) for i in camera.transpose(self.rect).topleft))
        # camera.surface.blit(self.surface, camera.transpose(self.rect).topleft)
        return True
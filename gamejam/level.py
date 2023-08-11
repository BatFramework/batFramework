import batFramework as bf
import pygame
from game_constants import GameConstants as gconst
from os.path import join
import utils.tools as tools
from math import sin
import itertools


chunk_res = (gconst.TILE_SIZE * gconst.CHUNK_SIZE,gconst.TILE_SIZE * gconst.CHUNK_SIZE)

def customize_tile(tile):...

class Tile(bf.AnimatedSprite):

    def __init__(self,x,y,tile_index: tuple[int,int],flip:tuple[bool,bool]=[False,False],tags=[]) -> None:
        super().__init__((gconst.TILE_SIZE,gconst.TILE_SIZE))
        # print(tile_index)
        self.rel_x, self.rel_y = 0,0
        self.set_position(x,y)
        # if tags : print(tags)
        self.flip = flip
        if tags : self.add_tag(*tags)
        self.tile_index = tile_index
        self.surface =bf.utils.get_tileset("tileset").get_tile(*tile_index,*self.flip)
        customize_tile(self)
    def __repr__(self) -> str:
        return f"pos:{self.rect.topleft}, index:{self.tile_index}, flip:{self.flip}, tags:{self.tags}"
    def process_event(self, event):
        pass
    def copy(self)->"Tile":
        return Tile(**self.serialize())
    def set_index(self,x,y):
        self.tile_index = (x,y)
        self.update_surface()
    def set_flip(self,flipX,flipY):
        self.flip = flipX,flipY
        print("set flip : ",self.flip)
        self.update_surface()
    def update_surface(self):
        self.surface =bf.utils.get_tileset("tileset").get_tile(*self.tile_index,*self.flip)
    
    def update_rel_pos(self):
        self.rel_x = self.rect.x % chunk_res[0]
        self.rel_y = self.rect.y % chunk_res[1]
    
    def set_position(self, x, y):
        super().set_position(x, y)
        self.update_rel_pos()
        return self
    def set_center(self, x, y):
        super().set_center(x, y)
        self.update_rel_pos()
        return self
    def update(self, dt: float):
        pass
    def draw(self, camera: bf.Camera) -> bool:
        # print(self.tile_index)
        if not self.visible : return 0
        camera.surface.blit(self.surface,camera.transpose(self.rect).topleft)
        return 1
    def serialize(self) -> dict:
        return {"x" :int(self.rect.left),"y" :int(self.rect.top),"tile_index":self.tile_index,"flip":self.flip,"tags":self.tags}
    def is_equal(self,other:"Tile"):
        return isinstance(other,Tile) and self.tile_index == other.tile_index and self.tags == other.tags and self.flip == other.flip        




def customize_tile(self: Tile):
    # return
    if not self.tags:
        return
    if self.has_tag("collider"):
        self.on_collideX = self.on_collideY = lambda collider,self=self: True
        if self.has_tag("one_way_up"):
            # print("customize ")
            self.on_collideY = lambda collider,self=self:collider.velocity.y > 0 and collider.rect.bottom < self.rect.centery#  [[collider.set_on_ground(True),collider.velocity.update(collider.velocity.x,0),False] if collider.velocity.y > 20 else False]
            self.on_collideX = lambda collider : False
    if self.has_tag("wave"):
        self.anchor_y = self.rect.top
        self.update = lambda dt: self.set_position(self.rect.x,self.anchor_y - (2*sin(pygame.time.get_ticks()*.01))) 
    if self.has_tag("bounce"):
        # self.process_event = lambda event: print("GOB")
        self.process_event = lambda event : bf.AudioManager().play_sound("jump") if event.type == gconst.STEP_ON_EVENT and event.entity.is_equal(self) else 0

class Chunk(bf.Entity):
    def __init__(self,x,y) -> None:
        super().__init__(chunk_res,surface_flags=0)
        # self.rect = pygame.Rect(*self.rect.topleft,*self.rect.size)
        self.grid_x = x
        self.grid_y = y
        self.set_position(x*chunk_res[0],y*chunk_res[1])
        self.size = gconst.CHUNK_SIZE
        self.tiles :dict[tuple,Tile]= {}
        self.dirty = True
        # self.surface.set_alpha(True)
        # self.surface.set_colorkey((255,0,255))
        self.surface = self.surface.convert_alpha()
        self.debug_surface = self.surface.copy()
        self.set_debug_color(bf.color.ORANGE)

    def load(self,data:dict):
        self.tiles = {eval(key):Tile(**value) for key,value in data.items()}
        _ =  [t.set_debug_color(bf.color.DARK_BLUE) for t in self.tiles.values() ]
        self.dirty = True
    def serialize(self)-> dict:
        return {"position": (self.grid_x,self.grid_y),"tiles" : {str(key):tile.serialize() for key,tile in self.tiles.items()}}

    def get_tile_at(self,gridx,gridy):
        try:
            return self.tiles[(gridx % gconst.CHUNK_SIZE,gridy % gconst.CHUNK_SIZE)]
        except KeyError:
            return None

    def get_tiles(self):
        return (t for t in self.tiles.values())
    
    def process_event(self, event):
        # print("chunk pevent")
        for t in self.get_tiles():
            t.process_event(event)

    def is_empty(self):
        return bool(self.tiles)
    
    def add_tile(self, x, y,tile_index,flip,*tags):
        """add new tile at global grid position"""
        tile_pos_x, tile_pos_y = x % gconst.CHUNK_SIZE, y % gconst.CHUNK_SIZE
        if (
            x < 0
            or y < 0
        ):
            return False
        # print(x,y)
        t = Tile(x * gconst.TILE_SIZE, y * gconst.TILE_SIZE,tile_index,flip,tags)
        t.set_debug_color(bf.color.DARK_BLUE)
        if (tile_pos_x,tile_pos_y) in self.tiles : 
            if  t.is_equal(self.get_tile_at(x,y)):
                return False
            self.tiles.pop((tile_pos_x,tile_pos_y))
        self.tiles[(tile_pos_x, tile_pos_y)] = t
        self.dirty = True
        return True

    def remove_tile(self,x,y):
        tile_pos_x, tile_pos_y = x % gconst.CHUNK_SIZE, y % gconst.CHUNK_SIZE
        if (
            tile_pos_x < 0
            or tile_pos_y < 0
        ) or (tile_pos_x,tile_pos_y) not in self.tiles:
            return False    
        t = self.tiles.pop((tile_pos_x,tile_pos_y))
        self.dirty = True
        return True
    
    def update_surf(self):
        # self.surface.fill((255,0,255))
        self.surface.fill((0,0,0,0))
        i = len(self.tiles)
        self.surface.fblits([(t.surface,(t.rel_x,t.rel_y)) for t in self.get_tiles()])
        self.debug_surface = self.surface.copy()
        for t in self.get_tiles():
            if t.has_tag("collider") :pygame.draw.rect(self.debug_surface,t._debug_color,(t.rel_x,t.rel_y,*t.rect.size),1)
        self.dirty = False    
        pygame.draw.rect(self.debug_surface,self._debug_color,(0,0,*self.rect.size),1)
        return i

    def draw(self, camera: bf.Camera) -> bool:
        if not self.visible or not self.surface or not camera.intersects(self.rect): return False
        i = 1
        if self.dirty:
            i += self.update_surf()
        return i
    def update(self,dt):
        for tile in self.get_tiles():
            tile.update(dt)


class Level(bf.Entity):
    def __init__(self, size=None, no_surface=True) -> None:
        super().__init__(size, no_surface)
        self.background_image = None
        self.chunks :dict[tuple[int,int],Chunk]= {}
        self.entities :list[bf.Entity]= []

    def set_background_image(self,path):
        self.background_image = pygame.image.load(join(bf.const.RESOURCE_PATH,path)).convert()


    def process_event(self, event): 
        for obj in itertools.chain(self.chunks.values(),self.entities):
            obj.process_event(event)

    def serialize(self)->dict:
        return {"chunks":[c.serialize() for c in self.chunks.values()],"entites":[e.serialize() for e in self.entities]}
    
    def load(self,data):
        self.chunks = {}
        self.entities = []
        for chunk in data["chunks"]:
            if not chunk["tiles"]: continue
            key = chunk["position"]
            tiles = chunk["tiles"]
            self.chunks[tuple(key)] = Chunk(*key)
            self.chunks[tuple(key)].load(tiles)
        for entity in data["entites"]:
            self.add_entity(Tile(**entity))
        return True
    
    def get_chunk_at(self,gridx,gridy):
        if gridx < 0 or gridy < 0: return None
        chunk_pos= tools.grid_to_chunk(gridx,gridy)
        if chunk_pos not in self.chunks: return None
        return self.chunks[chunk_pos]
    
    def get_data(self):
        return len(self.chunks),sum(len(c.tiles) for c in self.chunks.values())
    
    def get_all_tiles(self):
        return sum((list(c.get_tiles()) for c in self.chunks.values()), [])

    def get_by_tag(self,tag):
        return [e for e in itertools.chain(list(self.get_all_tiles()),self.get_entites()) if e.has_tag(tag)]


    def get_entites(self):
        return self.entities

    def get_tile_at(self,gridx,gridy):
        c = self.get_chunk_at(gridx,gridy)
        if not c : return None
        return c.get_tile_at(gridx,gridy)

    def add_entity(self,entity:bf.Entity):
        if entity in self.entities : return False
        self.entities.append(entity)
        return True
    def remove_entity(self,entity):
        try :
            self.entities.remove(entity)
            return True
        except ValueError:
            return False
    def update(self, dt: float):
        for entity in itertools.chain(self.entities ,list(self.chunks.values())):
            entity.update(dt)


    def add_tile(self,gridx,gridy,tile_index,flip,*tags):
        """
        x,y world coords
        Add a new tile at global grid position 
        Inserts a chunk if needed
        """
        chunk = self.get_chunk_at(gridx,gridy)
        if not chunk:
            chunk = Chunk(*tools.grid_to_chunk(gridx,gridy))
            self.chunks[tools.grid_to_chunk(gridx,gridy)] = chunk
        return chunk.add_tile(gridx,gridy,tile_index,flip,*tags)
    
    def remove_tile(self,gridx,gridy):
        """
        x,y world coords
        Removes an existing tile at global grid position 
        """

        c = self.get_chunk_at(gridx,gridy)
        if not c: return False
        res = c.remove_tile(gridx,gridy)
        if res: 
            if len(c.tiles) == 0:
                self.chunks.pop(tools.grid_to_chunk(gridx,gridy))
        return res

    def get_neighboring_tiles(self,gridx:int,gridy:int):
        res = []
        for x in range(gridx-2,gridx+2):
            for y in range(gridy-2,gridy+2):
                t = self.get_tile_at(x,y)
                if not t : continue
                res.append(t)
        return res

    def get_neighboring_entities(self,worldx,worldy,range):
        rect = pygame.FRect(0,0,range*2,range*2)
        rect.center = (worldx,worldy)
        return [e for e in self.entities if rect.colliderect(e.rect)]

    def draw(self, camera: bf.Camera) -> bool:
        i=0
        for chunk in self.chunks.values():
            i+= chunk.draw(camera)
        i += sum(entity.draw(camera) for entity in self.entities)
        if self.parent_scene.get_sharedVar("is_debugging_func")() == 2:
            camera.surface.fblits([(c.debug_surface,camera.transpose(c.rect).topleft) for c in self.chunks.values()])
            for entity in self.get_neighboring_entities(*camera.rect.center,camera.rect.w//2):
                pygame.draw.rect(camera.surface,entity._debug_color,camera.transpose(entity.rect),1)

        else:
            camera.surface.fblits([(c.surface,camera.transpose(c.rect).topleft) for c in self.chunks.values()])
        return i
    

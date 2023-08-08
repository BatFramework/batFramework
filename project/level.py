import batFramework as bf
import pygame
from game_constants import GameConstants as gconst
from os.path import join
 

chunk_res = (gconst.TILE_SIZE * gconst.CHUNK_SIZE,gconst.TILE_SIZE * gconst.CHUNK_SIZE)


def world_to_grid(x,y):
    return x//gconst.TILE_SIZE, y//gconst.TILE_SIZE

def grid_to_world(x,y):
    return x * gconst.TILE_SIZE, y * gconst.TILE_SIZE

def grid_to_chunk(x,y):
    return x//gconst.CHUNK_SIZE, y//gconst.CHUNK_SIZE

class Tile(bf.Entity):
    def __init__(self,x,y,tile_index: tuple[int,int]) -> None:
        super().__init__((gconst.TILE_SIZE,gconst.TILE_SIZE))
        self.rel_x, self.rel_y = 0,0
        self.set_position(x,y)
        self.add_tag("collider")
        self.tile_index = tile_index
        self.surface =bf.utils.get_tileset("tileset").get_tile(*tile_index)
    def update_rel_pos(self):
        self.rel_x = self.rect.x % chunk_res[0]
        self.rel_y = self.rect.y % chunk_res[1]
    def set_position(self, x, y):
        super().set_position(x, y)
        self.update_rel_pos()
    def set_center(self, x, y):
        super().set_center(x, y)
        self.update_rel_pos()
    def update(self, dt: float):
        pass
    def draw(self, camera: bf.Camera) -> bool:
        return 0

    def serialize(self) -> dict:
        return {"position" : self.rect.topleft,"index":self.tile_index}
class InteractiveTile(Tile):
    def __init__(self, x, y) -> None:
        super().__init__(x, y)

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
        self.tiles = {key:Tile(value) for key,value in data.items()} 
        self.dirty = True
    def serialize(self)-> dict:
        return {key:value for key,value in self.tiles.items()}

    def get_tile_at(self,gridx,gridy):
        try:
            return self.tiles[(gridx % gconst.CHUNK_SIZE,gridy % gconst.CHUNK_SIZE)]
        except KeyError:
            return None

    def get_tiles(self):
        return self.tiles.values()

    def is_empty(self):
        return bool(self.tiles)
    
    def add_tile(self, x, y,tile_index):
        """add new tile at global grid position"""
        tile_pos_x, tile_pos_y = x % gconst.CHUNK_SIZE, y % gconst.CHUNK_SIZE
        if (
            tile_pos_x < 0
            or tile_pos_x >= self.size
            or tile_pos_y < 0
            or tile_pos_y >= self.size
        ) or (tile_pos_x,tile_pos_y) in self.tiles:
            return False
        t = Tile(x * gconst.TILE_SIZE, y * gconst.TILE_SIZE,tile_index)
        self.tiles[(tile_pos_x, tile_pos_y)] = t
        self.dirty = True
        return True

    def remove_tile(self,x,y):
        tile_pos_x, tile_pos_y = x % gconst.CHUNK_SIZE, y % gconst.CHUNK_SIZE
        if (
            tile_pos_x < 0
            or tile_pos_x >= self.size
            or tile_pos_y < 0
            or tile_pos_y >= self.size
        ) or (tile_pos_x,tile_pos_y) not in self.tiles:
            return False    
        t = self.tiles.pop((tile_pos_x,tile_pos_y))
        self.dirty = True
        return True
    
    def update_surf(self):
        # self.surface.fill((255,0,255))
        self.surface.fill((0,0,0,0))
        i = len(self.tiles)
        self.surface.fblits([(t.surface,(t.rel_x,t.rel_y)) for t in self.tiles.values()])
        self.debug_surface = self.surface.copy()
        for t in self.tiles.values():
            pygame.draw.rect(self.debug_surface,"purple",(t.rel_x,t.rel_y,*t.rect.size),1)
        self.dirty = False    
        pygame.draw.rect(self.debug_surface,self._debug_color,(0,0,*self.rect.size),1)
        return i

    def draw(self, camera: bf.Camera) -> bool:
        if not self.visible or not self.surface or not camera.intersects(self.rect): return False
        i = 1
        if self.dirty:
            i += self.update_surf()
        return i

class Level(bf.Entity):
    def __init__(self, size=None, no_surface=True) -> None:
        super().__init__(size, no_surface)
        self.background_image = None
        
    def set_background_image(self,path):
        self.background_image = pygame.image.load(join(bf.const.RESOURCE_PATH,path)).convert()

    def serialize(self)->dict:
        return [c.serialize() for c in self.chunks.values()]
    
    def do_when_added(self):
        bf.utils.get_tileset("tileset")
        self.chunks :dict[tuple[int,int],Chunk]= {}
        for x in range(0,gconst.CHUNK_SIZE*4):
            self.add_tile(x,gconst.CHUNK_SIZE)

    def get_chunk_at(self,gridx,gridy):
        if gridx < 0 or gridy < 0: return None
        chunk_pos= grid_to_chunk(gridx,gridy)
        if chunk_pos not in self.chunks: return None
        return self.chunks[chunk_pos]
    
    def get_data(self):
        return len(self.chunks),sum(len(c.tiles) for c in self.chunks.values())
    
    def get_all_tiles(self):
        return sum((list(c.get_tiles()) for c in self.chunks.values()), [])
        
    def get_tile_at(self,gridx,gridy):
        c = self.get_chunk_at(gridx,gridy)
        if not c : return None
        return c.get_tile_at(gridx,gridy)

    def add_tile(self,gridx,gridy):
        """
        x,y world coords
        Add a new tile at global grid position 
        Inserts a chunk if needed
        """
        tile_index = (6,0)

        chunk = self.get_chunk_at(gridx,gridy)
        if not chunk:
            chunk = Chunk(*grid_to_chunk(gridx,gridy))
            self.chunks[grid_to_chunk(gridx,gridy)] = chunk
        return chunk.add_tile(gridx,gridy,tile_index)
        
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
                self.chunks.pop(grid_to_chunk(gridx,gridy))
        return res

    def get_neighboring_tiles(self,gridx:int,gridy:int):
        res = []
        for x in range(gridx-2,gridx+2):
            for y in range(gridy-2,gridy+2):
                t = self.get_tile_at(x,y)
                if not t : continue
                res.append(t)
        return res


    def draw(self, camera: bf.Camera) -> bool:
        i = 0
        for chunk in self.chunks.values():
            i+= chunk.draw(camera)
        # camera.surface.blit(self.surface, camera.transpose(self.rect))
        if self.parent_scene.get_sharedVar("is_debugging_func")() == 2:
            camera.surface.fblits([(c.debug_surface,camera.transpose(c.rect).topleft) for c in self.chunks.values()])
        else:
            camera.surface.fblits([(c.surface,camera.transpose(c.rect).topleft) for c in self.chunks.values()])
        return i
    

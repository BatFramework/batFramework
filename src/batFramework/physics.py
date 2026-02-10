"""
Physics module for batFramework
Provides opt-in AABB collision detection and resolution with gravity support.
"""

import pygame
from pygame.math import Vector2
from typing import Callable, Self, Iterator, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    import batFramework as bf


@dataclass(slots=True)
class Collision:
    """AABB collision result data"""
    entity_a: "bf.Entity"
    entity_b: "bf.Entity"
    overlap: Vector2       # Penetration depth (x, y)
    normal: Vector2        # Collision normal direction (points from b to a)
    
    @property
    def mtv(self) -> Vector2:
        """Minimum Translation Vector to resolve collision"""
        return Vector2(
            self.overlap.x * self.normal.x,
            self.overlap.y * self.normal.y
        )


class CollisionLayer:
    """Group of collidable entities that interact with each other"""
    
    def __init__(self, name: str):
        self.name = name
        self.static: list["bf.Entity"] = []           # Don't move (walls, platforms)
        self.dynamic: list["bf.DynamicEntity"] = []   # Move and respond to physics
    
    def clear(self):
        """Remove all entities from this layer"""
        self.static.clear()
        self.dynamic.clear()


class SpatialHash:
    """
    Grid-based spatial partitioning for efficient collision queries.
    Use for scenes with many (100+) collidable entities.
    """
    
    def __init__(self, cell_size: int = 64):
        self.cell_size = cell_size
        self.cells: dict[tuple[int, int], set["bf.Entity"]] = {}
    
    def _get_cells(self, rect: pygame.FRect) -> Iterator[tuple[int, int]]:
        """Get all cells a rect overlaps"""
        x1 = int(rect.left // self.cell_size)
        y1 = int(rect.top // self.cell_size)
        x2 = int(rect.right // self.cell_size)
        y2 = int(rect.bottom // self.cell_size)
        
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                yield (x, y)
    
    def insert(self, entity: "bf.Entity"):
        """Add entity to spatial hash"""
        for cell in self._get_cells(entity.rect):
            if cell not in self.cells:
                self.cells[cell] = set()
            self.cells[cell].add(entity)
    
    def remove(self, entity: "bf.Entity"):
        """Remove entity from spatial hash"""
        for cell in self._get_cells(entity.rect):
            if cell in self.cells:
                self.cells[cell].discard(entity)
    
    def update(self, entity: "bf.Entity", old_rect: pygame.FRect):
        """Update entity position in hash (call after moving)"""
        # Remove from old cells
        for cell in self._get_cells(old_rect):
            if cell in self.cells:
                self.cells[cell].discard(entity)
        # Add to new cells
        self.insert(entity)
    
    def query(self, rect: pygame.FRect) -> set["bf.Entity"]:
        """Get all entities potentially overlapping rect"""
        result = set()
        for cell in self._get_cells(rect):
            if cell in self.cells:
                result.update(self.cells[cell])
        return result
    
    def query_nearby(self, entity: "bf.Entity") -> set["bf.Entity"]:
        """Get all entities in the same cells as entity"""
        result = self.query(entity.rect)
        result.discard(entity)
        return result
    
    def clear(self):
        """Clear all cells"""
        self.cells.clear()
    
    def rebuild(self, entities: list["bf.Entity"]):
        """Full rebuild - call when entities move significantly"""
        self.clear()
        for e in entities:
            self.insert(e)


class PhysicsWorld:
    """
    Manages physics simulation for a scene.
    
    Features:
    - Gravity
    - AABB collision detection and resolution
    - Collision layers with configurable interactions
    - Collision callbacks
    - Optional spatial hashing for performance
    
    Usage:
        physics = bf.PhysicsWorld(gravity=(0, 980))
        physics.add_layer("player")
        physics.add_layer("platforms")
        physics.set_layers_collide("player", "platforms")
        physics.add_dynamic("player", player_entity)
        physics.add_static("platforms", *platform_entities)
        
        # In scene update:
        physics.update(dt)
    """
    
    def __init__(self, gravity: tuple[float, float] = (0, 980)):
        """
        Initialize physics world.
        
        Args:
            gravity: Gravity vector (x, y) in pixels/second². 
                     Default (0, 980) is roughly Earth gravity at 100px = 1m scale.
        """
        self.gravity = Vector2(gravity)
        self.collision_layers: dict[str, CollisionLayer] = {}
        self.layer_matrix: set[tuple[str, str]] = set()  # Which layer pairs collide
        self.callbacks: dict[tuple[str, str], Callable[[Collision], None]] = {}
        
        # Optional spatial partitioning
        self.spatial_hash: SpatialHash | None = None
        self._use_spatial_hash = False
    
    def enable_spatial_hash(self, cell_size: int = 64) -> Self:
        """
        Enable spatial hashing for better performance with many entities.
        
        Args:
            cell_size: Size of grid cells in pixels. Should be slightly larger
                      than your largest entity for best performance.
        """
        self.spatial_hash = SpatialHash(cell_size)
        self._use_spatial_hash = True
        # Rebuild hash with existing entities
        for layer in self.collision_layers.values():
            for entity in layer.static:
                self.spatial_hash.insert(entity)
            for entity in layer.dynamic:
                self.spatial_hash.insert(entity)
        return self
    
    def disable_spatial_hash(self) -> Self:
        """Disable spatial hashing"""
        self._use_spatial_hash = False
        if self.spatial_hash:
            self.spatial_hash.clear()
        self.spatial_hash = None
        return self
    
    def add_layer(self, name: str) -> Self:
        """Add a collision layer"""
        if name not in self.collision_layers:
            self.collision_layers[name] = CollisionLayer(name)
        return self
    
    def remove_layer(self, name: str) -> Self:
        """Remove a collision layer and all its entities"""
        if name in self.collision_layers:
            layer = self.collision_layers.pop(name)
            if self._use_spatial_hash and self.spatial_hash:
                for entity in layer.static:
                    self.spatial_hash.remove(entity)
                for entity in layer.dynamic:
                    self.spatial_hash.remove(entity)
            # Clean up layer matrix
            self.layer_matrix = {
                pair for pair in self.layer_matrix 
                if name not in pair
            }
        return self
    
    def set_layers_collide(self, layer_a: str, layer_b: str, collide: bool = True) -> Self:
        """
        Set whether two layers should check collisions between each other.
        
        Args:
            layer_a: First layer name
            layer_b: Second layer name  
            collide: True to enable collisions, False to disable
        """
        key = tuple(sorted([layer_a, layer_b]))
        if collide:
            self.layer_matrix.add(key)
        else:
            self.layer_matrix.discard(key)
        return self
    
    def layers_collide(self, layer_a: str, layer_b: str) -> bool:
        """Check if two layers are set to collide"""
        key = tuple(sorted([layer_a, layer_b]))
        return key in self.layer_matrix
    
    def set_collision_callback(
        self, 
        layer_a: str, 
        layer_b: str, 
        callback: Callable[[Collision], None]
    ) -> Self:
        """
        Set callback when entities from these layers collide.
        
        Args:
            layer_a: First layer name
            layer_b: Second layer name
            callback: Function called with Collision data when collision occurs
        """
        key = tuple(sorted([layer_a, layer_b]))
        self.callbacks[key] = callback
        return self
    
    def remove_collision_callback(self, layer_a: str, layer_b: str) -> Self:
        """Remove collision callback between two layers"""
        key = tuple(sorted([layer_a, layer_b]))
        self.callbacks.pop(key, None)
        return self
    
    def add_static(self, layer: str, *entities: "bf.Entity") -> Self:
        """
        Add static (non-moving) entities to a layer.
        Static entities don't have physics applied but can be collided with.
        """
        if layer not in self.collision_layers:
            self.add_layer(layer)
        self.collision_layers[layer].static.extend(entities)
        if self._use_spatial_hash and self.spatial_hash:
            for entity in entities:
                self.spatial_hash.insert(entity)
        return self
    
    def add_dynamic(self, layer: str, *entities: "bf.DynamicEntity") -> Self:
        """
        Add dynamic (moving) entities to a layer.
        Dynamic entities have gravity and collision resolution applied.
        """
        if layer not in self.collision_layers:
            self.add_layer(layer)
        self.collision_layers[layer].dynamic.extend(entities)
        if self._use_spatial_hash and self.spatial_hash:
            for entity in entities:
                self.spatial_hash.insert(entity)
        return self
    
    def remove(self, *entities: "bf.Entity") -> Self:
        """Remove entities from all layers"""
        for entity in entities:
            for layer in self.collision_layers.values():
                if entity in layer.static:
                    layer.static.remove(entity)
                if entity in layer.dynamic:
                    layer.dynamic.remove(entity)
            if self._use_spatial_hash and self.spatial_hash:
                self.spatial_hash.remove(entity)
        return self
    
    def clear(self) -> Self:
        """Remove all entities from all layers"""
        for layer in self.collision_layers.values():
            layer.clear()
        if self._use_spatial_hash and self.spatial_hash:
            self.spatial_hash.clear()
        return self
    
    def clear_layer(self, layer_name: str) -> Self:
        """Remove all entities from a specific layer"""
        if layer_name in self.collision_layers:
            layer = self.collision_layers[layer_name]
            if self._use_spatial_hash and self.spatial_hash:
                for entity in layer.static:
                    self.spatial_hash.remove(entity)
                for entity in layer.dynamic:
                    self.spatial_hash.remove(entity)
            layer.clear()
        return self
    
    @staticmethod
    def aabb_check(a: pygame.FRect, b: pygame.FRect) -> Collision | None:
        """
        Check for AABB collision between two rects.
        
        Returns:
            Collision object if colliding, None otherwise.
            Note: entity_a and entity_b will be None (rect-only check)
        """
        # Calculate overlap on each axis
        dx = a.centerx - b.centerx
        dy = a.centery - b.centery
        
        overlap_x = (a.width + b.width) / 2 - abs(dx)
        overlap_y = (a.height + b.height) / 2 - abs(dy)
        
        if overlap_x <= 0 or overlap_y <= 0:
            return None
        
        # Determine collision normal (smallest penetration axis)
        if overlap_x < overlap_y:
            normal = Vector2(1 if dx > 0 else -1, 0)
            overlap = Vector2(overlap_x, 0)
        else:
            normal = Vector2(0, 1 if dy > 0 else -1)
            overlap = Vector2(0, overlap_y)
        
        return Collision(
            entity_a=None,
            entity_b=None,
            overlap=overlap,
            normal=normal
        )
    
    def check_collision(
        self, 
        entity_a: "bf.Entity", 
        entity_b: "bf.Entity"
    ) -> Collision | None:
        """
        Check for collision between two entities.
        
        Returns:
            Collision object if colliding, None otherwise.
        """
        result = self.aabb_check(entity_a.rect, entity_b.rect)
        if result:
            result.entity_a = entity_a
            result.entity_b = entity_b
        return result
    
    def _get_collision_candidates(
        self, 
        entity: "bf.Entity", 
        layer: CollisionLayer
    ) -> Iterator["bf.Entity"]:
        """Get entities that could potentially collide with entity"""
        if self._use_spatial_hash and self.spatial_hash:
            nearby = self.spatial_hash.query_nearby(entity)
            for other in layer.static:
                if other in nearby:
                    yield other
            for other in layer.dynamic:
                if other in nearby and other is not entity:
                    yield other
        else:
            yield from layer.static
            for other in layer.dynamic:
                if other is not entity:
                    yield other
    
    def _find_entity_layer(self, entity: "bf.Entity") -> str | None:
        """Find which layer an entity belongs to"""
        for layer_name, layer in self.collision_layers.items():
            if entity in layer.static or entity in layer.dynamic:
                return layer_name
        return None
    
    def _trigger_callback(
        self, 
        layer_a: str, 
        layer_b: str, 
        collision: Collision
    ):
        """Trigger collision callback if one exists"""
        key = tuple(sorted([layer_a, layer_b]))
        callback = self.callbacks.get(key)
        if callback:
            callback(collision)
    
    def update(self, dt: float):
        """
        Update physics simulation.
        
        1. Apply gravity to dynamic entities
        2. Move entities by velocity
        3. Detect and resolve collisions
        
        Args:
            dt: Delta time in seconds
        """
        if dt <= 0:
            return
        
        # Collect all dynamic entities with their layer names
        dynamics: list[tuple[str, "bf.DynamicEntity"]] = []
        for layer_name, layer in self.collision_layers.items():
            for entity in layer.dynamic:
                dynamics.append((layer_name, entity))
        
        # 1. Apply gravity to all dynamic entities
        for _, entity in dynamics:
            if not getattr(entity, 'ignore_collisions', False):
                entity.velocity += self.gravity * dt
        
        # 2. Move and resolve collisions for each dynamic entity
        for entity_layer, entity in dynamics:
            if getattr(entity, 'ignore_collisions', False):
                entity.move_by_velocity(dt)
                continue
            
            old_rect = entity.rect.copy() if self._use_spatial_hash else None
            
            # Move X axis
            entity.rect.x += entity.velocity.x * dt
            self._resolve_axis(entity, entity_layer, 'x')
            
            # Move Y axis
            entity.rect.y += entity.velocity.y * dt
            self._resolve_axis(entity, entity_layer, 'y')
            
            # Update spatial hash
            if self._use_spatial_hash and self.spatial_hash and old_rect:
                self.spatial_hash.update(entity, old_rect)
    
    def _resolve_axis(
        self, 
        entity: "bf.DynamicEntity", 
        entity_layer: str, 
        axis: str
    ):
        """Resolve collisions for one axis"""
        import batFramework as bf
        
        # Check against all layers this entity's layer collides with
        for other_layer_name, other_layer in self.collision_layers.items():
            if not self.layers_collide(entity_layer, other_layer_name):
                continue
            
            # Check against all candidates in this layer
            for other in self._get_collision_candidates(entity, other_layer):
                collision = self.check_collision(entity, other)
                if not collision:
                    continue
                
                # Resolve based on axis
                resolved = False
                if axis == 'x' and collision.overlap.x > 0:
                    entity.rect.x += collision.overlap.x * collision.normal.x
                    
                    # Call entity hook
                    if isinstance(entity, bf.DynamicEntity):
                        if not entity.on_collideX(other):
                            entity.velocity.x = 0
                    else:
                        entity.velocity.x = 0
                    resolved = True
                    
                elif axis == 'y' and collision.overlap.y > 0:
                    entity.rect.y += collision.overlap.y * collision.normal.y
                    
                    # Call entity hook
                    if isinstance(entity, bf.DynamicEntity):
                        if not entity.on_collideY(other):
                            entity.velocity.y = 0
                    else:
                        entity.velocity.y = 0
                    resolved = True
                
                # Trigger callback
                if resolved:
                    self._trigger_callback(entity_layer, other_layer_name, collision)
    
    def raycast(
        self, 
        origin: tuple[float, float], 
        direction: tuple[float, float], 
        max_distance: float = float('inf'),
        layers: list[str] | None = None
    ) -> tuple["bf.Entity", float, Vector2] | None:
        """
        Cast a ray and find the first entity it hits.
        
        Args:
            origin: Ray start point (x, y)
            direction: Ray direction (will be normalized)
            max_distance: Maximum ray length
            layers: List of layer names to check (None = all layers)
        
        Returns:
            Tuple of (entity, distance, hit_point) or None if no hit
        """
        origin = Vector2(origin)
        direction = Vector2(direction)
        if direction.length_squared() == 0:
            return None
        direction = direction.normalize()
        
        closest_hit = None
        closest_dist = max_distance
        
        target_layers = layers if layers else list(self.collision_layers.keys())
        
        for layer_name in target_layers:
            if layer_name not in self.collision_layers:
                continue
            layer = self.collision_layers[layer_name]
            
            for entity in layer.static + layer.dynamic:
                result = self._ray_vs_aabb(origin, direction, entity.rect, closest_dist)
                if result and result[0] < closest_dist:
                    closest_dist = result[0]
                    closest_hit = (entity, result[0], result[1])
        
        return closest_hit
    
    @staticmethod
    def _ray_vs_aabb(
        origin: Vector2, 
        direction: Vector2, 
        rect: pygame.FRect, 
        max_dist: float
    ) -> tuple[float, Vector2] | None:
        """Ray vs AABB intersection test"""
        # Avoid division by zero
        dir_x = direction.x if direction.x != 0 else 1e-10
        dir_y = direction.y if direction.y != 0 else 1e-10
        
        t1 = (rect.left - origin.x) / dir_x
        t2 = (rect.right - origin.x) / dir_x
        t3 = (rect.top - origin.y) / dir_y
        t4 = (rect.bottom - origin.y) / dir_y
        
        tmin = max(min(t1, t2), min(t3, t4))
        tmax = min(max(t1, t2), max(t3, t4))
        
        if tmax < 0 or tmin > tmax or tmin > max_dist:
            return None
        
        t = tmin if tmin >= 0 else tmax
        if t > max_dist:
            return None
        
        hit_point = origin + direction * t
        return (t, hit_point)
    
    def query_rect(
        self, 
        rect: pygame.FRect, 
        layers: list[str] | None = None
    ) -> list["bf.Entity"]:
        """
        Find all entities overlapping a rectangle.
        
        Args:
            rect: Query rectangle
            layers: List of layer names to check (None = all layers)
        
        Returns:
            List of overlapping entities
        """
        results = []
        target_layers = layers if layers else list(self.collision_layers.keys())
        
        for layer_name in target_layers:
            if layer_name not in self.collision_layers:
                continue
            layer = self.collision_layers[layer_name]
            
            if self._use_spatial_hash and self.spatial_hash:
                candidates = self.spatial_hash.query(rect)
                for entity in candidates:
                    if entity in layer.static or entity in layer.dynamic:
                        if rect.colliderect(entity.rect):
                            results.append(entity)
            else:
                for entity in layer.static + layer.dynamic:
                    if rect.colliderect(entity.rect):
                        results.append(entity)
        
        return results
    
    def query_point(
        self, 
        point: tuple[float, float], 
        layers: list[str] | None = None
    ) -> list["bf.Entity"]:
        """
        Find all entities containing a point.
        
        Args:
            point: Query point (x, y)
            layers: List of layer names to check (None = all layers)
        
        Returns:
            List of entities containing the point
        """
        results = []
        target_layers = layers if layers else list(self.collision_layers.keys())
        
        for layer_name in target_layers:
            if layer_name not in self.collision_layers:
                continue
            layer = self.collision_layers[layer_name]
            
            for entity in layer.static + layer.dynamic:
                if entity.rect.collidepoint(point):
                    results.append(entity)
        
        return results


# Convenience functions for simple collision checks without PhysicsWorld

def check_aabb(a: pygame.FRect, b: pygame.FRect) -> bool:
    """Simple AABB overlap check"""
    return a.colliderect(b)


def get_overlap(a: pygame.FRect, b: pygame.FRect) -> tuple[float, float] | None:
    """
    Get overlap between two AABBs.
    
    Returns:
        (overlap_x, overlap_y) or None if no collision
    """
    dx = abs(a.centerx - b.centerx)
    dy = abs(a.centery - b.centery)
    
    overlap_x = (a.width + b.width) / 2 - dx
    overlap_y = (a.height + b.height) / 2 - dy
    
    if overlap_x > 0 and overlap_y > 0:
        return (overlap_x, overlap_y)
    return None


def find_collisions(
    entity: "bf.Entity", 
    candidates: list["bf.Entity"]
) -> list["bf.Entity"]:
    """Find all entities from candidates that collide with entity"""
    return [
        e for e in candidates 
        if e is not entity and entity.rect.colliderect(e.rect)
    ]

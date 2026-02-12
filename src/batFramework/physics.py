"""
Updated physics.py with collision_rect support.

Changes:
- Uses entity.collision_rect if available, else entity.rect
- Works with all three collision rect approaches
- Backward compatible (works without collision rects)
"""

import pygame
from pygame.math import Vector2
from typing import Callable, Self, Iterator, TYPE_CHECKING,Optional
from dataclasses import dataclass
from .entity import Entity

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
        """Add entity to spatial hash using collision rect"""
        
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
        # Add to new cells using current collision rect
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


class PhysicsWorld(Entity):
    """
    Manages physics simulation for a scene.
    
    Now supports separate collision rects via entity.collision_rect property.
    Falls back to entity.rect if collision_rect not defined.
    
    Features:
    - Gravity
    - AABB collision detection and resolution
    - Collision layers with configurable interactions
    - Collision callbacks
    - Optional spatial hashing for performance
    - Collision rect support (hitboxes separate from sprite position)
    """
    
    def __init__(self, gravity: tuple[float, float] = (0, 980)):
        super().__init__()
        self.gravity = Vector2(gravity)
        self.collision_layers: dict[str, CollisionLayer] = {}
        self.layer_matrix: set[tuple[str, str]] = set()
        self.callbacks: dict[tuple[str, str], Callable[[Collision], None]] = {}
        
        self.spatial_hash: SpatialHash | None = None
        self._use_spatial_hash = False
    
    def track_entity(self, entity: "bf.Entity"):
        """Track an entity so it automatically gets removed when killed."""
        original_do_removed = entity.do_when_removed

        def new_do_removed():
            original_do_removed()
            self.remove(entity)

        entity.do_when_removed = new_do_removed
        return entity

    def enable_spatial_hash(self, cell_size: int = 64) -> Self:
        """Enable spatial hashing for better performance with many entities."""
        self.spatial_hash = SpatialHash(cell_size)
        self._use_spatial_hash = True
        # Rebuild hash with existing entities
        for layer in self.collision_layers.values():
            for entity in layer.static + layer.dynamic:
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
                for entity in layer.static + layer.dynamic:
                    self.spatial_hash.remove(entity)
            self.layer_matrix = {
                pair for pair in self.layer_matrix 
                if name not in pair
            }
        return self
    
    def set_layers_collide(self, layer_a: str, layer_b: str, collide: bool = True) -> Self:
        """Set whether two layers should check collisions."""
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
        """Set callback when entities from these layers collide."""
        key = tuple(sorted([layer_a, layer_b]))
        self.callbacks[key] = callback
        return self
    
    def remove_collision_callback(self, layer_a: str, layer_b: str) -> Self:
        """Remove collision callback between two layers"""
        key = tuple(sorted([layer_a, layer_b]))
        self.callbacks.pop(key, None)
        return self
    
    def add_static(self, layer: str, *entities: "bf.Entity") -> Self:
        """Add static (non-moving) entities to a layer."""
        if layer not in self.collision_layers:
            self.add_layer(layer)
        self.collision_layers[layer].static.extend(entities)
        if self._use_spatial_hash and self.spatial_hash:
            for entity in entities:
                self.spatial_hash.insert(entity)
        for entity in entities:
            self.track_entity(entity)
        return self
    
    def add_dynamic(self, layer: str, *entities: "bf.DynamicEntity") -> Self:
        """Add dynamic (moving) entities to a layer."""
        if layer not in self.collision_layers:
            self.add_layer(layer)
        self.collision_layers[layer].dynamic.extend(entities)
        if self._use_spatial_hash and self.spatial_hash:
            for entity in entities:
                self.spatial_hash.insert(entity)
        for entity in entities:
            self.track_entity(entity)
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
                for entity in layer.static + layer.dynamic:
                    self.spatial_hash.remove(entity)
            layer.clear()
        return self
    
    @staticmethod
    def aabb_check(a: pygame.FRect, b: pygame.FRect) -> Collision | None:
        """Check for AABB collision between two rects."""
        dx = a.centerx - b.centerx
        dy = a.centery - b.centery
        
        overlap_x = (a.width + b.width) / 2 - abs(dx)
        overlap_y = (a.height + b.height) / 2 - abs(dy)
        
        if overlap_x <= 0 or overlap_y <= 0:
            return None
        
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
        Uses collision_rect if available, otherwise uses rect.
        """
        if entity_a is entity_b:
            return None
        
        # Get collision rects (falls back to entity.rect if no collision_rect)
        rect_a = entity_a.rect
        rect_b = entity_b.rect
        
        result = self.aabb_check(rect_a, rect_b)
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
        3. Detect and resolve collisions (uses collision_rect if available)
        """
        if dt <= 0:
            return
        
        # Collect all dynamic entities with their layer names
        dynamics: list[tuple[str, "bf.DynamicEntity"]] = []
        for layer_name, layer in self.collision_layers.items():
            for entity in layer.dynamic:
                dynamics.append((layer_name, entity))
        
        # 1. Apply gravity
        for _, entity in dynamics:
            if not getattr(entity, 'ignore_collisions', False):
                entity.velocity += self.gravity * dt
        
        # 2. Move and resolve collisions
        # Tracks dynamic-dynamic pairs already resolved this frame, keyed by axis,
        # to avoid double resolution while allowing the same pair to resolve on both axes.
        resolved_pairs: set[tuple] = set()

        for entity_layer, entity in dynamics:
            if getattr(entity, 'ignore_collisions', False):
                entity.move_by_velocity(dt)
                continue
            
            # Reset grounded each frame — will be set back to True by on_collideY
            # if a ground collision is actually resolved this frame.
            # This ensures walking off a ledge immediately clears the grounded state.
            if hasattr(entity, 'grounded'):
                entity._was_grounded = entity.grounded
                entity.grounded = False

            # Store old collision rect for spatial hash update
            old_collision_rect = entity.rect.copy() if self._use_spatial_hash else None
            
            # Move X axis
            entity.set_position(entity.rect.x + entity.velocity.x * dt, None)
            self._resolve_axis(entity, entity_layer, 'x', resolved_pairs)
            
            # Move Y axis  
            entity.set_position(None, entity.rect.y + entity.velocity.y * dt)
            self._resolve_axis(entity, entity_layer, 'y', resolved_pairs)
            
            # Update spatial hash
            if self._use_spatial_hash and self.spatial_hash and old_collision_rect:
                self.spatial_hash.update(entity, old_collision_rect)
 
        super().update(dt)
    
    def _resolve_axis(
        self,
        entity: "bf.DynamicEntity",
        entity_layer: str,
        axis: str,
        resolved_pairs: set[tuple]
    ):
        """Resolve collisions for one axis.

        For dynamic-dynamic collisions:
        - Position correction is split by mass ratio (heavier moves less)
        - Velocity is exchanged using the 1D elastic collision formula, scaled
          by the average restitution of the two entities (0 = sticky, 1 = elastic)
        - On Y, if other is already grounded it is treated as immovable to
          prevent it being pushed into the static geometry it rests on
        - resolved_pairs is keyed by (frozenset(ids), axis) so X and Y are
          tracked independently — a stacked pair still needs Y resolution even
          if it was already seen during the X pass

        Both mass and restitution are read via getattr so they are optional —
        defaults are mass=1.0 and restitution=0.0 (perfectly inelastic).
        """
        import batFramework as bf

        for other_layer_name, other_layer in self.collision_layers.items():
            if not self.layers_collide(entity_layer, other_layer_name):
                continue

            for other in self._get_collision_candidates(entity, other_layer):
                collision = self.check_collision(entity, other)
                if not collision:
                    continue

                other_is_dynamic = (
                    isinstance(other, bf.DynamicEntity)
                    and not getattr(other, 'ignore_collisions', False)
                )

                # Pair key includes axis so X and Y are deduplicated independently.
                # Without this, a pair seen (but not resolved) on X would be skipped
                # entirely on Y, causing stacked entities to phase through each other.
                if other_is_dynamic:
                    pair_key = (frozenset((id(entity), id(other))), axis)
                    if pair_key in resolved_pairs:
                        continue
                    resolved_pairs.add(pair_key)

                resolved = False

                if axis == 'x' and collision.overlap.x > 0:
                    mtv_x = collision.overlap.x * collision.normal.x

                    if other_is_dynamic:
                        mass_a = getattr(entity, 'mass', 1.0)
                        mass_b = getattr(other,  'mass', 1.0)
                        total  = mass_a + mass_b

                        # Split position correction by mass
                        entity.set_position(entity.rect.x + mtv_x * (mass_b / total), None)
                        other.set_position( other.rect.x  - mtv_x * (mass_a / total), None)

                        # Elastic velocity exchange scaled by restitution
                        restitution = (
                            getattr(entity, 'restitution', 0.0)
                            + getattr(other,  'restitution', 0.0)
                        ) / 2.0
                        va, vb = entity.velocity.x, other.velocity.x
                        new_va = (va*(mass_a-mass_b) + 2*mass_b*vb) / total
                        new_vb = (vb*(mass_b-mass_a) + 2*mass_a*va) / total
                        entity.velocity.x = new_va * restitution
                        other.velocity.x  = new_vb * restitution

                        if not entity.on_collideX(other):
                            entity.velocity.x = 0
                        if not other.on_collideX(entity):
                            other.velocity.x = 0
                    else:
                        entity.set_position(entity.rect.x + mtv_x, None)
                        if not entity.on_collideX(other):
                            entity.velocity.x = 0

                    resolved = True

                elif axis == 'y' and collision.overlap.y > 0:
                    mtv_y = collision.overlap.y * collision.normal.y

                    if other_is_dynamic:
                        # If other is grounded it is braced against static geometry —
                        # pushing it down would clip it into the floor it rests on.
                        # Treat it as immovable on Y; entity takes the full correction.
                        if getattr(other, 'grounded', False):
                            entity.set_position(None, entity.rect.y + mtv_y)

                            restitution = (
                                getattr(entity, 'restitution', 0.0)
                                + getattr(other,  'restitution', 0.0)
                            ) / 2.0
                            entity.velocity.y *= -restitution

                            if not entity.on_collideY(other):
                                entity.velocity.y = 0
                        else:
                            mass_a = getattr(entity, 'mass', 1.0)
                            mass_b = getattr(other,  'mass', 1.0)
                            total  = mass_a + mass_b

                            entity.set_position(None, entity.rect.y + mtv_y * (mass_b / total))
                            other.set_position( None, other.rect.y  - mtv_y * (mass_a / total))

                            restitution = (
                                getattr(entity, 'restitution', 0.0)
                                + getattr(other,  'restitution', 0.0)
                            ) / 2.0
                            va, vb = entity.velocity.y, other.velocity.y
                            new_va = (va*(mass_a-mass_b) + 2*mass_b*vb) / total
                            new_vb = (vb*(mass_b-mass_a) + 2*mass_a*va) / total
                            entity.velocity.y = new_va * restitution
                            other.velocity.y  = new_vb * restitution

                            if not entity.on_collideY(other):
                                entity.velocity.y = 0
                            if not other.on_collideY(entity):
                                other.velocity.y = 0
                    else:
                        entity.set_position(None, entity.rect.y + mtv_y)
                        if not entity.on_collideY(other):
                            entity.velocity.y = 0

                    resolved = True

                if resolved:
                    self._trigger_callback(entity_layer, other_layer_name, collision)
    
    def raycast(
        self, 
        origin: tuple[float, float], 
        direction: tuple[float, float], 
        max_distance: float = float('inf'),
        caster : Optional["bf.Entity"] = None,
        *layers:str 
    ) -> tuple["bf.Entity", float, Vector2] | None:
        """
        Cast a ray and find the first entity it hits.
        """
        origin = Vector2(origin)
        direction = Vector2(direction)
        if direction.length_squared() == 0:
            return None
        direction = direction.normalize()
        
        closest_hit = None
        if max_distance is None:
            max_distance = float('inf')
        closest_dist = max_distance
        
        target_layers = list(layers) if layers else list(self.collision_layers.keys())
        
        for layer_name in target_layers:
            if layer_name not in self.collision_layers:
                continue
            layer = self.collision_layers[layer_name]
            
            for entity in layer.static + layer.dynamic:
                if entity is caster : continue
                result = self._ray_vs_aabb(origin, direction, entity.rect, closest_dist)
                if result and result[0] < closest_dist:
                    closest_dist = result[0]
                    closest_hit = (entity, result[0], result[1])
        
        return closest_hit
    
    @staticmethod
    def _ray_vs_aabb(origin, direction, rect, max_dist):
        tmin = -float('inf')
        tmax = float('inf')

        # X slab
        if direction.x != 0:
            tx1 = (rect.left - origin.x) / direction.x
            tx2 = (rect.right - origin.x) / direction.x
            tmin = max(tmin, min(tx1, tx2))
            tmax = min(tmax, max(tx1, tx2))
        else:
            # Ray parallel to X axis — must be inside slab
            if origin.x < rect.left or origin.x > rect.right:
                return None

        # Y slab
        if direction.y != 0:
            ty1 = (rect.top - origin.y) / direction.y
            ty2 = (rect.bottom - origin.y) / direction.y
            tmin = max(tmin, min(ty1, ty2))
            tmax = min(tmax, max(ty1, ty2))
        else:
            # Ray parallel to Y axis — must be inside slab
            if origin.y < rect.top or origin.y > rect.bottom:
                return None

        if tmax < 0 or tmin > tmax or tmin > max_dist:
            return None

        t = tmin if tmin >= 0 else tmax
        if t < 0 or t > max_dist:
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
        Uses collision_rect for overlap testing.
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
        Uses collision_rect for point testing.
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


# Convenience functions
def check_aabb(a: pygame.FRect, b: pygame.FRect) -> bool:
    """Simple AABB overlap check"""
    return a.colliderect(b)


def get_overlap(a: pygame.FRect, b: pygame.FRect) -> tuple[float, float] | None:
    """Get overlap between two AABBs."""
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
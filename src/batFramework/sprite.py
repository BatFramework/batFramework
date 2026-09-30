import batFramework as bf
import pygame
from functools import wraps
from typing import Self, Callable


def marks_dirty(*attrs: str):
    """Mark the given compute stages as dirty after calling the method"""

    def wrapper(func: Callable):
        @wraps(func)
        def inner(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            for attr in attrs:
                self.dirty[attr] = True
            return result

        return inner

    return wrapper


def check_dirty(attr: str):
    """Only run the method if the stage is dirty, then mark it clean"""

    def wrapper(func: Callable):
        @wraps(func)
        def inner(self, *args, **kwargs):
            if not self.dirty.get(attr, False):
                return None
            self.dirty[attr] = False
            return func(self, *args, **kwargs)

        return inner

    return wrapper


class Sprite(bf.Drawable):
    def __init__(
        self,
        path=None,
        size: None | tuple[int, int] = None,
        convert_alpha: bool = True,
    ):
        # compute stages, in order: original_surface -> size -> flip -> surface
        self.dirty: dict[str, bool] = {"size": False, "flip": False}
        self.original_surface: pygame.Surface = None
        self._resized_surface: pygame.Surface = None
        self.rotation: int = 0
        self.rotation_anchor = (0, 0)
        self.flip = (False, False)
        super().__init__(convert_alpha=convert_alpha)
        if path is not None:
            self.from_path(path)
        if size is not None:
            self.set_size(size)

    @marks_dirty("flip")
    def set_flip(self, flipx, flipy) -> Self:
        self.flip = (flipx, flipy)
        return self

    @marks_dirty("size")
    def set_size(self, size: tuple[float, float]) -> Self:
        super().set_size(size)
        return self

    def from_path(self, path: str) -> Self:
        tmp = bf.ResourceManager().get_image(path, self.convert_alpha)
        if tmp is None:
            return self
        return self.from_surface(tmp)

    @marks_dirty("size")
    def from_surface(self, surface: pygame.Surface) -> Self:
        if surface is None:
            return self
        self.original_surface = surface
        self.set_size(surface.get_size())
        return self

    @check_dirty("size")
    def compute_resize(self):
        if self.original_surface is None:
            return
        size = (int(self.rect.w), int(self.rect.h))
        if self.original_surface.get_size() == size:
            # copy so later alpha changes don't alter the shared resource image
            self._resized_surface = self.original_surface.copy()
        else:
            self._resized_surface = pygame.transform.scale(self.original_surface, size)
        # flip has to be reapplied on the fresh surface
        self.dirty["flip"] = True

    @check_dirty("flip")
    def compute_flip(self):
        if self._resized_surface is None:
            return
        alpha = self.surface.get_alpha()
        if any(self.flip):
            self.surface = pygame.transform.flip(self._resized_surface, *self.flip)
        else:
            self.surface = self._resized_surface
        if alpha is not None:
            self.surface.set_alpha(alpha)

    def compute(self):
        self.compute_resize()
        self.compute_flip()

    def get_blit_data(self, camera):
        self.compute()
        return super().get_blit_data(camera)

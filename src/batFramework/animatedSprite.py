import batFramework as bf
import pygame


# info needed
# source image
# frame length_list = [1,2,1,5]


def search_index(target, lst):
    running_sum = 0
    for i, value in enumerate(lst):
        running_sum += value
        if running_sum >= target:
            return i
    return -1


class AnimState:
    def __init__(self, file, width, height, frame_length_list) -> None:
        self.frames: list[pygame.Surface] = bf.utils.img_slice(file, width, height)
        self.frames_flipX: list[pygame.Surface] = bf.utils.img_slice(
            file, width, height, True
        )

        self.frame_length_list = frame_length_list

    def get_frame_index(self, counter):
        return search_index(int(counter), self.frame_length_list)

    def get_frame(self, counter, flip):
        i = self.get_frame_index(counter)
        return self.frames_flipX[i] if flip else self.frames[i]


class AnimatedSprite(bf.Entity):
    def __init__(self, size=None) -> None:
        super().__init__(size, no_surface=True)
        self.float_counter = 0
        self.animStates: dict[str, AnimState] = {}
        self.current_animState = ""
        self.flipX = False
        self._locked = False

    def lock_animState(self):
        self._locked = True

    def unlock_animState(self):
        self._locked = False

    def set_flipX(self, value):
        self.flipX = value

    def add_animState(
        self, name: str, file: str, size: tuple[int, int], frame_length_list: list[int]
    ):
        if name in self.animStates:
            return
        self.animStates[name] = AnimState(file, *size, frame_length_list)

    def set_animState(self, state, reset_counter=True, lock=False):
        if state not in self.animStates or self._locked:
            return False
        self.current_animState = state
        self.rect = (
            self.animStates[self.current_animState]
            .frames[0]
            .get_frect(center=self.rect.center)
        )
        if reset_counter or self.float_counter > sum(
            self.get_state().frame_length_list
        ):
            self.float_counter = 0
        if lock:
            self.lock_animState()
        return True

    def get_state(self):
        if self.current_animState not in self.animStates:
            return None
        return self.animStates[self.current_animState]

    def get_frame_index(self):
        return self.animStates[self.current_animState].get_frame_index(
            self.float_counter
        )

    def update(self, dt: float):
        self.float_counter += 60 * dt
        if self.float_counter > sum(self.get_state().frame_length_list):
            self.float_counter = 0

    def draw(self, camera: bf.Camera) -> bool:
        if not self.visible or not camera.intersects(self.rect) or not self.animStates:
            return False
        # pygame.draw.rect(camera.surface,"purple",camera.transpose(self.rect).move(2,2))
        camera.surface.blit(
            self.get_state().get_frame(self.float_counter, self.flipX),
            camera.transpose(self.rect),
        )
        return True

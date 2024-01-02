import batFramework as bf
import pygame


def search_index(target, lst):
    cumulative_sum = 0
    for index, value in enumerate(lst):
        cumulative_sum += value
        if cumulative_sum >= target:
            return index
    return -1


class AnimState:
    def __init__(
        self, name: str, file, width, height, frame_length_list: list | int
    ) -> None:
        self.frames: list[pygame.Surface] = bf.utils.img_slice(file, width, height)
        self.frames_flipX: list[pygame.Surface] = bf.utils.img_slice(
            file, width, height, True
        )
        self.name = name
        self.frame_length_list = []
        self.ffl_length = 0
        self.set_frame_length_list(frame_length_list)

    def __repr__(self):
        return f"AnimState({self.name})"

    def get_frame_index(self, counter: float | int):
        return search_index(int(counter % self.ffl_length), self.frame_length_list)

    def get_frame(self, counter, flip):
        i = self.get_frame_index(counter)
        return self.frames_flipX[i] if flip else self.frames[i]

    def set_frame_length_list(self, frame_length_list: list[int] | int):
        if isinstance(frame_length_list, int):
            frame_length_list = [frame_length_list] * len(self.frames)
        if len(frame_length_list) != len(self.frames):
            raise ValueError("frame_length_list should have values for all frames")
        self.frame_length_list = frame_length_list
        self.ffl_length = sum(self.frame_length_list)


class AnimatedSprite(bf.DynamicEntity):
    def __init__(self, size=None) -> None:
        super().__init__(size, no_surface=True)
        self.float_counter = 0
        self.animStates: dict[str, AnimState] = {}
        self.current_animState: str = ""
        self.flipX = False
        self._locked = False

    def set_counter(self, value: float):
        self.float_counter = value

    def lock_animState(self):
        self._locked = True

    def unlock_animState(self):
        self._locked = False

    def set_flipX(self, value):
        self.flipX = value

    def remove_animState(self, name: str):
        if not name in self.animStates:
            return
        self.animStates.pop(name)
        if self.current_animState == name:
            self.current_animState = (
                list(self.animStates.keys())[0] if self.animStates else ""
            )

    def add_animState(
        self, name: str, file: str, size: tuple[int, int], frame_length_list: list[int]
    ):
        if name in self.animStates:
            return
        self.animStates[name] = AnimState(name, file, *size, frame_length_list)
        if len(self.animStates) == 1:
            self.set_animState(name)

    def set_animState(self, state: str, reset_counter=True, lock=False):
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
        return self.animStates.get(self.current_animState, None)

    def get_frame_index(self):
        return self.animStates[self.current_animState].get_frame_index(
            self.float_counter
        )

    def update(self, dt: float):
        if not self.animStates:
            return
        self.float_counter += 60 * dt
        if self.float_counter > self.get_state().ffl_length:
            self.float_counter = 0
        self.do_update(dt)

    def draw(self, camera: bf.Camera) -> bool:
        if not self.visible or not camera.intersects(self.rect) or not self.animStates:
            return False
        # pygame.draw.rect(camera.surface,"purple",camera.transpose(self.rect).move(2,2))
        camera.surface.blit(
            self.get_state().get_frame(self.float_counter, self.flipX),
            camera.transpose(self.rect),
        )
        return True

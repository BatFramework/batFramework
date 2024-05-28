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
        self,
        name: str,
        surface: pygame.Surface,
        width,
        height,
        duration_list: list | int,
    ) -> None:
        self.frames: list[pygame.Surface] = list(
            bf.utils.split_surface(
                surface, width, height, False, convert_alpha
            ).values()
        )
        self.frames_flipX: list[pygame.Surface] = list(
            bf.utils.split_surface(surface, width, height, True, convert_alpha).values()
        )

        self.name = name
        self.duration_list: list[int] = []
        self.duration_list_length = 0
        self.set_duration_list(duration_list)

    def __repr__(self):
        return f"AnimState({self.name})"

    def counter_to_frame(self, counter: float | int) -> int:
        return search_index(
            int(counter % self.duration_list_length), self.duration_list
        )

    def get_frame(self, counter, flip):
        i = self.counter_to_frame(counter)
        return self.frames_flipX[i] if flip else self.frames[i]

    def set_duration_list(self, duration_list: list[int] | int):
        if isinstance(duration_list, int):
            duration_list = [duration_list] * len(self.frames)
        if len(duration_list) != len(self.frames):
            raise ValueError("duration_list should have values for all frames")
        self.duration_list = duration_list
        self.duration_list_length = sum(self.duration_list)


class AnimatedSprite(bf.DynamicEntity):
    def __init__(self, size=None) -> None:
        super().__init__(size, no_surface=True)
        self.float_counter: float = 0
        self.animStates: dict[str, AnimState] = {}
        self.current_state: AnimState | None = None
        self.flipX = False
        self._locked = False
        self.paused: bool = False

    def pause(self) -> None:
        self.paused = True

    def resume(self) -> None:
        self.paused = False

    def toggle_pause(self) -> None:
        self.paused = not self.paused

    def set_counter(self, value: float) -> None:
        self.float_counter = value

    def set_frame(self, frame_index: int) -> None:
        if not self.current_state:
            return
        total = sum(self.current_state.duration_list)
        frame_index = max(0, min(total, frame_index))
        new_counter = 0
        i = 0
        while frame_index < total:
            if self.current_state.counter_to_frame(new_counter) >= frame_index:
                break
            new_counter += self.current_state.duration_list[i]
            i += 1
        self.set_counter(new_counter)

    def lock(self) -> None:
        self._locked = True

    def unlock(self) -> None:
        self._locked = False

    def set_flipX(self, value) -> None:
        self.flipX = value

    def remove_animState(self, name: str) -> bool:
        if not name in self.animStates:
            return False
        self.animStates.pop(name)
        if self.current_state and self.current_state.name == name:
            self.current_animState = (
                list(self.animStates.keys())[0] if self.animStates else ""
            )
        return True

    def add_animState(
        self,
        name: str,
        surface: pygame.Surface,
        size: tuple[int, int],
        duration_list: list[int],
        convert_alpha: bool = True,
    ) -> bool:
        if name in self.animStates:
            return False
        self.animStates[name] = AnimState(name, surface, *size, duration_list)
        if len(self.animStates) == 1:
            self.set_animState(name)
        return True

    def set_animState(self, state: str, reset_counter=True, lock=False) -> bool:
        if state not in self.animStates or self._locked:
            return False

        animState = self.animStates[state]
        self.current_state = animState

        self.rect = self.current_state.frames[0].get_frect(center=self.rect.center)

        if reset_counter or self.float_counter > sum(animState.duration_list):
            self.float_counter = 0
        if lock:
            self.lock()
        return True

    def get_animState(self) -> AnimState | None:
        return self.current_state

    def update(self, dt: float) -> None:
        s = self.get_animState()
        if not self.animStates or s is None:
            return
        if not self.paused:
            self.float_counter += 60 * dt
            if self.float_counter > s.duration_list_length:
                self.float_counter = 0
        self.do_update(dt)

    def draw(self, camera: bf.Camera) -> int:
        if (
            not self.visible
            or not camera.rect.colliderect(self.rect)
            or not self.current_state
        ):
            return 0
        camera.surface.blit(
            self.current_state.get_frame(self.float_counter, self.flipX),
            camera.world_to_screen(self.rect),
        )
        return 1

import batFramework as bf
import pygame
import random


class Manager(bf.SceneManager):
    def __init__(self, *initial_scene_list) -> None:
        # random.seed("random")
        super().__init__()
        self._screen: pygame.Surface | None = bf.const.SCREEN
        self._timeManager = bf.TimeManager()
        self._cutsceneManager = bf.CutsceneManager()
        self._cutsceneManager.set_manager(self)
        self._clock: pygame.Clock = pygame.Clock()
        pygame.mouse.set_cursor(bf.const.DEFAULT_CURSOR)
        self.do_pre_init()
        self.init_scenes(*initial_scene_list)
        self.set_sharedVar("clock", self._clock)
        self.do_init()

    @staticmethod
    def set_icon(path: str) -> None:
        surf = pygame.image.load(bf.ResourceManager().get_path(path)).convert_alpha()
        pygame.display.set_icon(surf)

    def print_status(self):
        super().print_status()
        print("TIMERS : ")
        for r in self._timeManager.get_active_registers():
            # print(r["timers"])
            print("\n".join(str(t) for t in r))
        print("-" * 40)

    def get_fps(self) -> float:
        return self._clock.get_fps()

    def do_init(self) -> None:
        pass

    def do_pre_init(self) -> None:
        pass

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        self._running = True
        dt: float = 0
        while self._running:
            for event in pygame.event.get():
                event.consumed = False
                self.process_event(event)
                if not event.consumed:
                    if event.type == pygame.QUIT:
                        self._running = False
                        break
                    if event.type == pygame.VIDEORESIZE and not (
                        bf.const.FLAGS & pygame.SCALED
                    ):
                        bf.const.set_resolution((event.w, event.h))
            # update
            dt = self._clock.tick(bf.const.FPS) / 1000
            # dt = min(dt, 0.02) dirty fix for dt being too high when window not focused for a long time
            self._timeManager.update(dt)
            self._cutsceneManager.update(dt)
            self.update(dt)
            # render
            self._screen.fill((0, 0, 0))
            self.draw(self._screen)
            pygame.display.flip()
        pygame.quit()

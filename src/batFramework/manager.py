import batFramework as bf
import pygame
import random


class Manager(bf.SceneManager):
    def __init__(self, *initial_scene_list) -> None:
        # random.seed("random")
        self._screen: pygame.Surface|None = bf.const.SCREEN
        self._timeManager = bf.TimeManager()
        self._cutsceneManager = bf.CutsceneManager(self)
        self._clock: pygame.Clock = pygame.Clock()
        super().__init__(*initial_scene_list)
        self.set_sharedVar("clock", self._clock)
        self.do_init()

    @staticmethod
    def set_icon(path: str):
        surf = pygame.image.load(bf.utils.get_path(path)).convert_alpha()
        pygame.display.set_icon(surf)

    def get_fps(self):
        return self._clock.get_fps()

    def do_init(self):
        pass

    def stop(self) -> None:
        self._running = False

    def run(self):
        self._running = True
        dt: float = 0
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    break
                if event.type == pygame.VIDEORESIZE:
                    bf.const.set_resolution((event.w, event.h))
                self.process_event(event)
            # update
            dt = self._clock.tick(bf.const.FPS if not bf.const.VSYNC else 0) / 1000
            # dt = min(dt, 0.02) dirty fix for dt being too high when window not focused for a long time
            self._cutsceneManager.update(dt)
            self._timeManager.update()
            self.update(dt)
            # render
            self.draw(self._screen)
            pygame.display.flip()
        pygame.quit()

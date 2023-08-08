import batFramework as bf
import pygame

class Manager(bf.SceneManager):
    def __init__(self,*initial_scene_list) -> None:
        self._screen: pygame.Surface = bf.const.SCREEN
        self._easing_manager = bf.EasingAnimationManager()
        self._timeManager = bf.Time()
        self._cutsceneManager = bf.CutsceneManager(self)
        print("Vsync : ",pygame.display.is_vsync())
        self._clock: pygame.Clock = pygame.Clock()
        super().__init__(*initial_scene_list)
        self.set_sharedVar("clock",self._clock)
        self.do_init()

    @staticmethod
    def set_icon(path:str):
        surf = pygame.image.load(bf.utils.get_path(path)).convert_alpha()
        pygame.display.set_icon(surf)

    @staticmethod
    def set_resource_path(path):
        bf.const.set_resource_path(path)

    def get_fps(self):
        return self._clock.get_fps()

    def do_init(self):
        pass

    def run(self):
        self._running = True
        dt: float = 0
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    break
                self.process_event(event)
            # update
            dt = self._clock.tick(bf.const.FPS) / 1000
            dt = min(dt,.02)
            self._easing_manager.update()
            self._timeManager.update()
            self._cutsceneManager.update(dt)
            self.update(dt)
            # render
            self.draw(self._screen)
            pygame.display.flip()
        pygame.quit()

import batFramework as bf
import pygame
import asyncio

class Manager(bf.SceneManager):
    def __init__(self, *initial_scene_list) -> None:
        super().__init__()
        self.debug_mode: bf.enums.debugMode = bf.debugMode.HIDDEN
        self.screen: pygame.Surface | None = bf.const.SCREEN
        self.timeManager = bf.TimeManager()
        self.cutsceneManager = bf.CutsceneManager()
        self.cutsceneManager.set_manager(self)
        self.clock: pygame.Clock = pygame.Clock()
        self.is_async_running : bool = False
        self.running = False
        pygame.mouse.set_cursor(bf.const.DEFAULT_CURSOR)
        self.do_pre_init()
        self.init_scenes(*initial_scene_list)
        bf.ResourceManager().set_sharedVar("clock", self.clock)
        bf.ResourceManager().set_sharedVar("debug_mode", self.debug_mode)

        self.do_init()

    @staticmethod
    def set_icon(path: str) -> None:
        surf = pygame.image.load(bf.ResourceManager().get_path(path)).convert_alpha()
        pygame.display.set_icon(surf)

    def print_status(self):
        """
        Print detailed information about the current state of the scenes, shared variables,
        and additional timers managed by the subclass.
        """
        # Call the parent class's print_status method to include its information
        super().print_status()
        
        # Add the timers information in a cohesive manner
        print("\n" + "=" * 50)
        print(" TIMERS".center(50))
        print("=" * 50)
        
        # Print the timers information
        print(self.timeManager)
        
        # End with a visual separator
        print("=" * 50 + "\n")


    def get_fps(self) -> float:
        return self.clock.get_fps()

    def do_init(self) -> None:
        pass

    def do_pre_init(self) -> None:
        pass

    def stop(self) -> None:
        self.running = False

    async def run_async(self):
        if self.running:
            print("Error : Already running")
            return
        self.is_async_running = True
        self.running = True
        dt: float = 0
        while self.running:
            for event in pygame.event.get():
                event.consumed = False
                self.process_event(event)
                if not event.consumed:
                    if event.type == pygame.QUIT:
                        self.running = False
                        break
                    if event.type == pygame.VIDEORESIZE and not (
                        bf.const.FLAGS & pygame.SCALED
                    ):
                        bf.const.set_resolution((event.w, event.h))
            # update
            self.timeManager.update(dt)
            self.cutsceneManager.update(dt)
            self.update(dt)
            # render
            self.screen.fill((0, 0, 0))
            self.draw(self.screen)
            pygame.display.flip()
            dt = self.clock.tick(bf.const.FPS) / 1000
            # dt = min(dt, 0.02) dirty fix for dt being too high when window not focused for a long time
            await asyncio.sleep(0)
        pygame.quit()


    def run(self) -> None:
        if self.running:
            print("Error : Already running")
            return
        self.running = True
        dt: float = 0
        while self.running:
            for event in pygame.event.get():
                event.consumed = False
                self.process_event(event)
                if not event.consumed:
                    if event.type == pygame.QUIT:
                        self.running = False
                        break
                    if event.type == pygame.VIDEORESIZE and not (
                        bf.const.FLAGS & pygame.SCALED
                    ):
                        bf.const.set_resolution((event.w, event.h))
            # update
            self.timeManager.update(dt)
            self.cutsceneManager.update(dt)
            self.update(dt)
            # render
            self.screen.fill((0, 0, 0))
            self.draw(self.screen)
            pygame.display.flip()
            dt = self.clock.tick(bf.const.FPS) / 1000
            # dt = min(dt, 0.02) dirty fix for dt being too high when window not focused for a long time
        pygame.quit()

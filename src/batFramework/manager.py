import batFramework as bf
from batFramework import const
import pygame
import asyncio
import logging

logger = logging.getLogger(__name__)

# frames longer than this (in seconds) are logged as stalls before dt is clamped
_STALL_THRESHOLD = 0.1


class Manager(bf.SceneManager):
    def __init__(self, *initial_scenes) -> None:
        super().__init__()
        self.context = bf.Context()
        self.screen: pygame.Surface | None = bf.const.SCREEN
        self.timeManager = bf.TimeManager()
        self.cutsceneManager = bf.CutsceneManager()
        self.cutsceneManager.set_manager(self)
        self.clock: pygame.Clock = pygame.Clock()
        self.is_async_running: bool = False
        self.running = False
        pygame.mouse.set_cursor(bf.const.DEFAULT_CURSOR)
        self.context.clock = self.clock
        sm = bf.gui.StyleManager()
        sm.init()

        self.do_pre_init()
        if initial_scenes:
            self.init_scenes(*initial_scenes)
        self.do_init()
        logger.debug(
            f"Manager initialized with {len(self.scenes)} scene(s): "
            f"{[s.name for s in self.scenes]}"
        )

    @staticmethod
    def set_icon(path: str) -> None:
        surf = pygame.image.load(bf.ResourceManager().get_path(path)).convert_alpha()
        pygame.display.set_icon(surf)
        logger.debug(f"Window icon set from '{path}'")

    def get_status(self) -> str:
        """
        Return detailed information about the current state of the scenes, shared variables,
        and timers.
        """
        return "\n".join(
            [
                super().get_status(),
                "=" * 50,
                " TIMERS".center(50),
                "=" * 50,
                str(self.timeManager),
                "=" * 50 + "\n",
            ]
        )

    def get_fps(self) -> float:
        return self.clock.get_fps()

    def do_init(self) -> None:
        pass

    def do_pre_init(self) -> None:
        pass

    def stop(self) -> None:
        logger.debug("Stop requested")
        self.running = False

    def process_event(self, event: pygame.Event):
        event.consumed = False
        keys = pygame.key.get_pressed()
        if (
            bf.const.ALLOW_DEBUG
            and keys[pygame.K_LCTRL]
            and keys[pygame.K_LSHIFT]
            and event.type == pygame.KEYDOWN
        ):
            if event.key == pygame.K_d:
                mode = self.cycle_debug_mode()
                logger.debug(f"Debug mode cycled to {mode.name}")
                return
            if event.key == pygame.K_p:
                self.print_status()
                return
        self.cutsceneManager.process_event(event)
        if event.type == pygame.VIDEORESIZE and not (bf.const.FLAGS & pygame.SCALED):
            logger.debug(f"Window resized to {event.w}x{event.h}")
            bf.const.set_resolution((event.w, event.h))
            self.screen = bf.const.SCREEN

        if event.consumed:
            return

        super().process_event(event)
        if not event.consumed:
            if event.type == pygame.QUIT:
                logger.debug("Quit event received, stopping")
                self.running = False

    def update(self, dt: float) -> None:
        self.timeManager.update(dt)
        self.cutsceneManager.update(dt)
        super().update(dt)
        bf.Context.last_dt = dt

    def _next_dt(self) -> float:
        dt = self.clock.tick(bf.const.FPS) / 1000
        if dt > _STALL_THRESHOLD:
            logger.debug(f"Frame stalled for {dt * 1000:.0f}ms, dt clamped")
        # fix for dt being too high when window not focused for a long time
        return min(dt, 0.1)

    async def _run_async_internal(self):
        if len(self.scenes) == 0:
            raise Exception("Manager can't start without scenes")
        if self.running:
            raise Exception("Error : Already running")
        self.is_async_running = True
        self.running = True
        logger.debug(
            f"Starting async main loop (fps limit: {bf.const.FPS or 'none'}, "
            f"scene: '{self.get_current_scene_name()}')"
        )
        dt: float = 0
        while self.running:
            for event in pygame.event.get():
                self.process_event(event)
            # update
            self.update(dt)
            # render
            self.draw(self.screen)
            pygame.display.flip()
            dt = self._next_dt()
            await asyncio.sleep(0)
        logger.debug("Async main loop ended, quitting pygame")
        pygame.quit()

    def run_async(self):
        asyncio.run(self._run_async_internal())

    def run(self) -> None:
        if len(self.scenes) == 0:
            raise Exception("Manager can't start without scenes")
        if self.running:
            raise Exception("Error : Already running")
        self.running = True
        logger.debug(
            f"Starting main loop (fps limit: {bf.const.FPS or 'none'}, "
            f"scene: '{self.get_current_scene_name()}')"
        )
        dt: float = 0
        while self.running:
            for event in pygame.event.get():
                self.process_event(event)
            # update
            self.update(dt)
            # render
            self.draw(self.screen)
            pygame.display.flip()
            dt = self._next_dt()
        logger.debug("Main loop ended, quitting pygame")
        pygame.quit()

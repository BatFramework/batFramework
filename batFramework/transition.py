import pygame
import batFramework as bf


class BaseTransition:
    def __init__(
        self,
        source_surf: pygame.Surface,
        dest_surf: pygame.Surface,
        duration=100,
        **kwargs,
    ) -> None:
        self.source = source_surf
        self.dest = dest_surf
        self.ended = False
        self.source_scene_name = ""
        self.dest_scene_name = ""
        self.duration = duration

    def set_source_name(self, name):
        self.source_scene_name = name

    def set_dest_name(self, name):
        self.dest_scene_name = name

    def update(self, dt):
        pass

    def draw(self, surface):
        pass

    def has_ended(self):
        return False

    def set_ended(self, val):
        self.ended = val


class FadeColorTransition(BaseTransition):
    def __init__(
        self,
        source_surf,
        dest_surf,
        duration=200,
        color_duration=200,
        color=bf.color.CLOUD_WHITE,
        **kwargs,
    ) -> None:
        super().__init__(source_surf, dest_surf, duration)
        self.target_time = duration * 2 + color_duration
        self.color_surf = pygame.Surface((source_surf.get_rect().size)).convert_alpha()
        self.color_surf.fill(color)
        self.ease_out = bf.EasingAnimation(
            bf.Easing.EASE_IN,
            duration,
            lambda x: self.color_surf.set_alpha(int(255 - (255 * x))),
            lambda: self.set_ended(True),
        )

        self.color_timer = bf.Time().timer(
            name="GOB",
            duration=color_duration,
            callback=lambda: [self.set_state("out"), self.ease_out.start()],
        )
        self.ease_in = bf.EasingAnimation(
            bf.Easing.EASE_IN,
            duration,
            update_callback=lambda x: self.color_surf.set_alpha(int(255 * x)),
            end_callback=lambda: [self.set_state("color"), self.color_timer.start()],
        )
        self.state = "in"
        self.ease_in.start()

    def set_state(self, state: str):
        self.state = state

    def update(self, dt):
        if self.state == "in":
            self.ease_in.update()
        elif self.state == "out":
            self.ease_out.update()

    def has_ended(self):
        return self.ended

    def draw(self, surface):
        if self.state != "color":
            surface.blit(self.source if self.state == "in" else self.dest, (0, 0))
        surface.blit(self.color_surf, (0, 0))


class FadeTransition(BaseTransition):
    def __init__(self, source_surf, dest_surf, duration=200) -> None:
        super().__init__(source_surf, dest_surf)
        self.start_ticks = pygame.time.get_ticks()
        self.target_time = duration
        self.progress = 0

    def has_ended(self):
        return self.ended

    def update(self, dt):
        seconds = pygame.time.get_ticks() - self.start_ticks
        self.progress = seconds / self.target_time
        if seconds >= self.target_time:
            self.ended = True

    def draw(self, surface):
        self.source.set_alpha(int(255 - (255 * self.progress)))
        self.dest.set_alpha(int(255 * self.progress))
        surface.blit(self.source, (0, 0))
        surface.blit(self.dest, (0, 0))


class SlideTransition(BaseTransition):
    def __init__(
        self,
        source_surf,
        dest_surf,
        duration=1000,
        source_alignment: bf.Alignment = bf.Alignment.BOTTOM,
        easing: bf.Easing = bf.Easing.EASE_IN_OUT,
        **kwargs,
    ) -> None:
        super().__init__(source_surf, dest_surf, duration)
        self.offset = pygame.Vector2(0, 0)
        if source_alignment in [bf.Alignment.TOP, bf.Alignment.BOTTOM]:
            self.offset.y = bf.const.RESOLUTION[1]
            if source_alignment == bf.Alignment.TOP:
                self.offset.y *= -1
        elif source_alignment in [bf.Alignment.LEFT, bf.Alignment.RIGHT]:
            self.offset.x = bf.const.RESOLUTION[0]
            if source_alignment == bf.Alignment.LEFT:
                self.offset.x *= -1
        else:
            self.offset.x = -bf.const.RESOLUTION[0]
            print(
                f"Unsupported Alignment : {source_alignment.value}, set to default : {bf.Alignment.LEFT.value} "
            )
        self.anim = bf.EasingAnimation(
            easing,
            duration,
            lambda x: self.update_offset(self.offset.lerp((0, 0), x)),
            lambda: self.set_ended(True),
        )
        self.anim.start()

    def update_offset(self, vec):
        self.offset.update(vec)

    def update(self, dt):
        self.anim.update()

    def has_ended(self):
        return self.ended

    def draw(self, surface):
        surface.blit(self.source, (0, 0))
        surface.blit(self.dest, self.offset)

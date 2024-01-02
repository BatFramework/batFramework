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
        self.index = 0

    def set_scene_index(self, index):
        self.index = index

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
        duration=600,
        color_duration=200,
        color=bf.color.CLOUD_WHITE,
        **kwargs,
    ) -> None:
        super().__init__(source_surf, dest_surf, duration)
        self.target_time = duration * 2 + color_duration
        self.color_surf = pygame.Surface((source_surf.get_rect().size)).convert_alpha()
        self.color_surf.fill(color)
        self.ease_out = bf.EasingAnimation(
            easing_function=bf.Easing.EASE_IN,
            duration=(duration - color_duration) // 2,
            update_callback=lambda x: self.color_surf.set_alpha(int(255 - (255 * x))),
            end_callback=lambda: self.set_ended(True),
        )

        self.color_timer = bf.Timer(
            duration=color_duration, end_callback=lambda: self.set_state("out")
        )
        self.ease_in = bf.EasingAnimation(
            easing_function=bf.Easing.EASE_IN,
            duration=(duration - color_duration) // 2,
            update_callback=lambda x: self.color_surf.set_alpha(int(255 * x)),
            # update_callback=lambda x: print(x),
            end_callback=lambda: self.set_state("color"),
        )
        self.state = None

        self.state = "in"
        self.ease_in.start()

    def set_state(self, state: str):
        self.state = state
        if state == "in":
            self.ease_in.start()
        elif state == "color":
            self.color_timer.start()
        elif state == "out":
            self.ease_out.start()

    def has_ended(self):
        return self.ended

    def set_ended(self, val):
        super().set_ended(val)

    def draw(self, surface):
        if self.state != "color":
            surface.blit(self.source if self.state == "in" else self.dest, (0, 0))
        surface.blit(self.color_surf, (0, 0))


class FadeTransition(BaseTransition):
    def __init__(self, source_surf, dest_surf, duration=500) -> None:
        super().__init__(source_surf, dest_surf)
        self.anim = bf.EasingAnimation(
            None,
            bf.Easing.EASE_IN_OUT,
            duration,
            self.update_surface,
            lambda: self.set_ended(True),
        )
        self.anim.start()

    def update_surface(self, progress):
        self.source.set_alpha(int(255 - (255 * progress)))
        self.dest.set_alpha(int(255 * progress))

    def has_ended(self):
        return self.ended

    def draw(self, surface):
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
            easing_function=easing,
            duration=duration,
            update_callback=lambda x: self.update_offset(self.offset.lerp((0, 0), x)),
            end_callback=lambda: self.set_ended(True),
        )
        self.anim.start()

    def update_offset(self, vec):
        self.offset.update(vec)

    def has_ended(self):
        return self.ended

    def draw(self, surface):
        surface.blit(self.source, (0, 0))
        surface.blit(self.dest, self.offset)

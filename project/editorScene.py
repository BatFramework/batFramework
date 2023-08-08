import batFramework as bf
from level import Level, world_to_grid
import pygame
import math
from pygame.math import Vector2
from math import ceil
from game_constants import GameConstants as gconst
class PreviewCursor(bf.Entity):
    def __init__(self) -> None:
        super().__init__((gconst.TILE_SIZE,gconst.TILE_SIZE))
        self.surface.convert_alpha()
        # self.surface.fill((0,0,0,0))
        # pygame.draw.rect(self.surface,"white",self.rect,2,5)
    def update(self, dt: float):
        self.set_center(*pygame.mouse.get_pos())



class EditorScene(bf.Scene):
    def __init__(self):
        super().__init__("editor")
        self.scroll_speed = 10
        self.sqrt2 = math.sqrt(2)
        self.velocity = Vector2()
        self.guide_lines_cache = {}



        editLabel = bf.Label("EDIT", 24)
        editLabel.set_position(self.hud_camera.rect.right - editLabel.rect.w, 0)




        self.add_hud_entity(editLabel)
        self.preview_cursor = PreviewCursor()
        self.add_hud_entity(self.preview_cursor)

    def do_when_added(self):
        self.level: Level = self.get_sharedVar("level")

        self.add_world_entity(self.level)
        self.camera.set_position(150, 150)

        exitAction = bf.Action("exit")
        exitAction.add_key_control(pygame.K_e)

        placePlayer = bf.Action("placePlayer")
        placePlayer.add_key_control(pygame.K_q)

        minus_zoom = bf.Action("minus_zoom")
        minus_zoom.add_key_control(pygame.K_n)
        minus_zoom.add_mouse_control(4)

        plus_zoom = bf.Action("plus_zoom")
        plus_zoom.add_key_control(pygame.K_m)
        plus_zoom.add_mouse_control(5)

        right = bf.Action("right")
        right.add_key_control(pygame.K_RIGHT, pygame.K_d)
        right.set_holding()

        left = bf.Action("left")
        left.add_key_control(pygame.K_LEFT, pygame.K_a)
        left.set_holding()

        up = bf.Action("up")
        up.add_key_control(pygame.K_UP, pygame.K_w)
        up.set_holding()

        down = bf.Action("down")
        down.add_key_control(pygame.K_DOWN, pygame.K_s)
        down.set_holding()

        mouse_click =bf.Action("l_click")
        mouse_click.add_mouse_control(1)
        mouse_click.set_holding()

        mouse_click2 = bf.Action("r_click")
        mouse_click2.add_mouse_control(3)
        mouse_click2.set_holding()

        self._action_container.add_action(
            right, left, up, down,
            exitAction,
            placePlayer,
            minus_zoom, plus_zoom,
            mouse_click2, mouse_click
        )

        self.debugger = bf.Debugger(self.manager)
        self.debugger.add_dynamic_data("Screen", pygame.mouse.get_pos)
        self.debugger.add_dynamic_data("World",
                                        lambda: [int(i) for i in self.camera.convert_screen_to_world(*pygame.mouse.get_pos())])
        self.debugger.add_dynamic_data("Grid",
                                        lambda: world_to_grid(*[int(i) for i in
                                                                self.camera.convert_screen_to_world(*pygame.mouse.get_pos())]))
        self.debugger.add_dynamic_data("Zoom",
                                       lambda : 1/self.camera.zoom_factor)
        self.add_hud_entity(self.debugger)

    def on_exit(self):
        self.get_sharedVar("mainCamera").set_center(*self.camera.rect.center)
        self.get_sharedVar("mainCamera").zoom(self.camera.zoom_factor)

    def on_enter(self):
        self.camera.set_center(*self.get_sharedVar("mainCamera").rect.center)
        self.camera.zoom(self.get_sharedVar("mainCamera").zoom_factor)

    def do_handle_event(self, event):
        self.velocity.update(0, 0)
        if self._action_container.is_active("exit"):
            self.manager.set_scene("main")
        if self._action_container.is_active("minus_zoom"):
            self.camera.zoom(self.camera.zoom_factor+1)
        if self._action_container.is_active("plus_zoom"):
            self.camera.zoom(1/(self.camera.zoom_factor * 0.5) )

        if self._action_container.is_active("right"):
            self.velocity.x = 1
        if self._action_container.is_active("left"):
            self.velocity.x += -1
        if self._action_container.is_active("up"):
            self.velocity.y += -1
        if self._action_container.is_active("down"):
            self.velocity.y += 1
        if self.velocity:
            self.velocity = self.velocity.normalize() * self.scroll_speed
        if self._action_container.is_active("l_click"):
            x, y = world_to_grid(*[int(i) for i in self.camera.convert_screen_to_world(*pygame.mouse.get_pos())])
            if all(i >= 0 for i in [x,y]):
                self.level.add_tile(x, y)
        if self._action_container.is_active("r_click"):
            x, y = world_to_grid(*[int(i) for i in self.camera.convert_screen_to_world(*pygame.mouse.get_pos())])
            self.level.remove_tile(x, y)

    def do_update(self, dt):
        self.camera.move(*self.velocity * (dt * 60))

    def draw_guide_lines(self):
        line_color = (180, 160, 160)
        line_alpha = 100
        width, height = self.camera.rect.size
        cols = int(width // gconst.TILE_SIZE) + 2
        rows = int(height // gconst.TILE_SIZE) + 2
        tmp_size = (cols * gconst.TILE_SIZE, rows * gconst.TILE_SIZE)
        tmp_surf = pygame.Surface(tmp_size).convert_alpha()
        # tmp_surf.set_colorkey("magenta")
        tmp_surf.set_colorkey((0,0,0,0))
        # tmp_surf.fill("magenta")
        tmp_surf.set_alpha(line_alpha)

        for col in range(cols):
            x = col * gconst.TILE_SIZE
            pygame.draw.line(tmp_surf, line_color, (x, 0), (x, tmp_size[1]), 1)
        for row in range(rows):
            y = row * gconst.TILE_SIZE
            pygame.draw.line(tmp_surf, line_color, (0, y), (tmp_size[0], y), 1)

        self.guide_lines_cache[self.camera.zoom_factor] = tmp_surf

    def do_post_world_draw(self, surface: pygame.Surface):
        if self.camera.zoom_factor not in self.guide_lines_cache:
            self.draw_guide_lines()
            print("Draw lines!")
        offset = Vector2(
            x=(ceil(self.camera.rect.left) % gconst.TILE_SIZE) ,# - const.TILE_SIZE,
            y=(ceil(self.camera.rect.top) % gconst.TILE_SIZE  ) #- const.TILE_SIZE
        )

        # surface.blit(self.guide_lines_cache[self.camera.zoom_factor], -offset)

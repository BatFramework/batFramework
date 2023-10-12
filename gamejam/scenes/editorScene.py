from .custom_scenes import CustomBaseScene
import batFramework as bf
import pygame
from pygame.math import Vector2
import utils.tools as tools
from level import Level, Tile
import itertools
from game_constants import GameConstants as gconst
import random
import cutscenes

class EditorScene(CustomBaseScene):
    def __init__(self) -> None:
        super().__init__("editor")

        self.add_action(
            bf.Action("l_click").add_mouse_control(1).set_holding(),
            bf.Action("r_click").add_mouse_control(3).set_holding(),
            bf.Action("middle_click").add_mouse_control(2),
            bf.Action("game_scene").add_key_control(pygame.K_e, pygame.K_ESCAPE),
            bf.Action("tile_picker").add_key_control(pygame.K_q),
            bf.Action("switch_tool").add_key_control(pygame.K_t),
            bf.Action("save").add_key_control(pygame.K_1),
            bf.Action("load").add_key_control(pygame.K_2),
            bf.Action("up").add_key_control(pygame.K_UP, pygame.K_w).set_holding(),
            bf.Action("down").add_key_control(pygame.K_DOWN, pygame.K_s).set_holding(),
            bf.Action("left").add_key_control(pygame.K_LEFT, pygame.K_a).set_holding(),
            bf.Action("right").add_key_control(pygame.K_RIGHT, pygame.K_d).set_holding(),
            bf.Action("control").add_key_control(pygame.K_LCTRL,pygame.K_RCTRL).set_holding()
        )


        self.tile_cursor: Tile = Tile(0, 0, (0, 0))
        self.tools = ["tile", "entity", "spawn"]
        self.tool_iterator = (i for i in itertools.count())
        next(self.tool_iterator)

        self.tool = None
        self.tool_label = bf.Label("")
        self.set_tool(self.tools[0])

        self.notif_label = bf.Label("")
        self.notif_label.set_visible(False)

        self.add_hud_entity(self.notif_label, self.tool_label)
        editor_label = bf.Label("EDITOR")
        self.notif_label.set_position(*self.tool_label.rect.bottomleft)

        self.add_hud_entity(editor_label)
        editor_label.set_position(
            *self.hud_camera.rect.move(-editor_label.rect.w, 0).topright
        )



        self.level: Level = None
        self.debugger: bf.Debugger = None


        self.pm = bf.ParticleManager()
        self.pm.render_order = 4
        self.add_world_entity(self.pm)

        self.camera_velocity = Vector2()

    def delete_effect_generate(self,start_pos):
        for _ in range(10):
            self.pm.add_particle(
                bf.Particle,
                start_pos=start_pos,
                start_vel = (random.uniform(-30,30),random.uniform(-30,30)),
                color = bf.color.LIGHT_GB,duration=300,
                size=(2,2)
            )
        bf.AudioManager().play_sound("delete")


    def cycle_flip(self, x, y):
        return not x, x != y

    def set_tool(self, tool: str):
        self.tool = tool
        self.tool_label.set_text(tool)
        self.tile_cursor.set_visible(tool != "spawn")

    def do_when_added(self):
        self.set_sharedVar("brush_tile", self.tile_cursor)
        self.add_hud_entity(self.tile_cursor)
        self.debugger = bf.Debugger(self.manager).set_outline(False)

        self.debugger.add_dynamic_data(
            "tags",
            lambda: "NaN"
            if self.level == None
            else "".join([t[0] for t in self.get_tile_tags(self.get_tile_at_mouse())]),
        )

        self.debugger.add_dynamic_data(
            "flip",
            lambda: "Nan"
            if (self.level is None or self.get_tile_at_mouse() is None)
            else self.get_tile_at_mouse().flip,
        )
        self.add_hud_entity(self.debugger)

    def get_tile_tags(self, tile: Tile):
        if not tile:
            return []
        return tile.tags

    def get_tile_at_mouse(self):
        if self.level == None:
            return None
        return self.level.get_tile_at(
            *tools.world_to_grid(
                *[
                    int(i)
                    for i in self.camera.convert_screen_to_world(
                        *pygame.mouse.get_pos()
                    )
                ]
            )
        )

    def on_enter(self):
        super().on_enter()
        shared = self.get_sharedVar("level")
        if self.level != shared:
            if self.level != None:
                self.remove_world_entity(self.level)
            self.level = shared
            self.add_world_entity(self.level)
        if self.manager._scenes[self.get_scene_index()+1]._name == "game":
            self.camera.set_center(*self.get_sharedVar("game_camera").rect.center)
            # bf.CutsceneManager().queue(cutscenes.EditorTutorial())

    def do_handle_event(self, event):
        if self.actions.is_active("switch_tool"):
            self.set_tool(self.tools[next(self.tool_iterator) % len(self.tools)])

        # SAVE/LOAD
        if self.actions.is_active("save"):
            data = self.level.serialize()
            res = bf.Utils.save_json_to_file("levels/level_0.json", data)
            self.notif_label.set_text("SAVED" if res else "ERROR")
            self.notif_label.set_visible(True)
            bf.Timer(
                duration=400, end_callback=lambda: self.notif_label.set_visible(False)
            ).start()
        elif self.actions.is_active("load"):
            res = tools.load_level(self.level, 0)
            self.notif_label.set_text("LOADED" if res else "ERROR")
            self.notif_label.set_visible(True)
            bf.Timer(
                duration=400, end_callback=lambda: self.notif_label.set_visible(False)
            ).start()

        # L CLICK / R CLICK
        if self.actions.is_active("l_click"):
            self.left_click()

        if self.actions.is_active("r_click"):
            self.right_click()


        # MIDDLE CLICK
        if self.actions.is_active("middle_click"):
            if self.actions.is_active("control"):
                self.camera.zoom(1)
            else:
                self.tile_cursor.set_flip(*self.cycle_flip(*self.tile_cursor.flip))

        # EXIT SCENE
        if self.actions.is_active("game_scene"):
            self.manager.transition_to_scene("game", bf.FadeTransition,duration=200)
        elif self.actions.is_active("tile_picker"):
            self.manager.transition_to_scene("tile_picker", bf.FadeTransition,duration =200)


        # ZOOM
        if self.actions.is_active("control") and event.type == pygame.MOUSEWHEEL:
            self.camera.zoom_by(abs(event.y) / event.y * 0.1)
    def do_update(self, dt):
        self.camera_velocity *= 0.65
        speed = 70 * dt

        if self.actions.is_active("left"):
            self.camera_velocity.x -= speed
        if self.actions.is_active("right"):
            self.camera_velocity.x += speed
        if self.actions.is_active("up"):

            self.camera_velocity.y -= speed
        if self.actions.is_active("down"):
            self.camera_velocity.y += speed


        self.camera.move(*self.camera_velocity)

        self.tile_cursor.rect.center = pygame.mouse.get_pos()

    # def do_post_world_draw(self, surface):
    #     x,y = self.camera.rect.topleft
    #     x,y = round(x),round(y)
    #     surface.fill("red",(0,x,-x,self.camera.rect.h))
    #     surface.fill("red",(0,0,self.camera.rect.w,-y))


    def left_click(self):
        x, y = tools.world_to_grid(
            *[
                int(i)
                for i in self.camera.convert_screen_to_world(
                    *pygame.mouse.get_pos()
                )
            ]
        )
        # if all(i >= 0 for i in [x,y]):
        brush_tile: Tile = self.get_sharedVar("brush_tile")
        match self.tool:
            case "tile":
                self.level.add_tile(
                    x, y, brush_tile.tile_index, brush_tile.flip, *brush_tile.tags
                )
            case "entity":
                if not self.level.get_neighboring_entities(
                    *self.camera.convert_screen_to_world(*pygame.mouse.get_pos()), 1
                ):
                    self.level.add_entity(
                        Tile(
                            **brush_tile.copy()
                            .set_position(
                                int(x * gconst.TILE_SIZE), int(y * gconst.TILE_SIZE)
                            )
                            .serialize()
                        )
                    )
    def right_click(self):
        x, y = tools.world_to_grid(
            *[
                int(i)
                for i in self.camera.convert_screen_to_world(
                    *pygame.mouse.get_pos()
                )
            ]
        )
        match self.tool:
            case "tile":
                
                if self.level.remove_tile(x, y):
                    self.delete_effect_generate(self.camera.convert_screen_to_world(*pygame.mouse.get_pos()))

            case "entity":
                tile = self.level.get_neighboring_entities(
                    *self.camera.convert_screen_to_world(*pygame.mouse.get_pos()), 1
                )
                if tile:
                    if self.level.remove_entity(tile[0]):
                        self.delete_effect_generate(self.camera.convert_screen_to_world(*pygame.mouse.get_pos()))


            case _:
                return

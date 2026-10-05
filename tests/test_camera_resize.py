"""Camera behavior when a resizable window changes size."""

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame
import batFramework as bf


class CameraResizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        bf.init((320, 240), flags=pygame.RESIZABLE)

    def test_set_size_keeps_viewport_origin_and_world_center(self):
        camera = bf.Camera(size=(320, 240))
        camera.rect.topleft = (12, 18)
        camera.set_center(900, 700)

        camera.set_size((640, 360))

        self.assertEqual(camera.rect, pygame.FRect(12, 18, 640, 360))
        self.assertEqual(camera.world_rect.center, (900, 700))
        self.assertEqual(camera.surface.get_size(), (640, 360))

    def test_videoresize_updates_every_scene_and_anchors_hud(self):
        first = bf.Scene("first")
        second = bf.Scene("second")
        first.camera.set_center(800, 600)
        second.camera.set_center(-200, 300)
        first.hud_camera.set_position(40, 50)
        first.root.set_position(40, 50)
        fixed = bf.Camera(size=(100, 80), fullscreen=False)
        second.add_layer("fixed", fixed)

        with patch("pygame.mouse.set_cursor"):
            manager = bf.Manager(first, second)
            manager.process_event(pygame.event.Event(
                pygame.VIDEORESIZE, w=640, h=360, size=(640, 360)))

        self.assertEqual(bf.const.RESOLUTION, (640, 360))
        self.assertIs(manager.screen, bf.const.SCREEN)
        for scene in (first, second):
            self.assertEqual(scene.camera.rect, pygame.FRect(0, 0, 640, 360))
            self.assertEqual(scene.hud_camera.rect, pygame.FRect(0, 0, 640, 360))
            self.assertEqual(scene.root.rect.size, (640, 360))
        self.assertEqual(first.camera.world_rect.center, (800, 600))
        self.assertEqual(second.camera.world_rect.center, (-200, 300))
        self.assertEqual(first.hud_camera.get_position(), (40, 50))
        self.assertEqual(first.root.rect.topleft, (40, 50))
        self.assertEqual(fixed.rect.size, (100, 80))


if __name__ == "__main__":
    unittest.main()

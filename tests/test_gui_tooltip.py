"""Tooltip state, root-owned layout, and repeated timer lifecycle regressions."""
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


class TooltipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((400, 240))
        bf.FontManager().init_font(None)

    def setUp(self):
        self.scene = bf.Scene(self.id())
        self.scene.flush_entity_changes()
        self.root = self.scene.root
        self.root.set_size((400, 240), force=True)
        self.camera = self.scene.hud_camera
        self.camera.set_size((400, 240)).set_position(0, 0)
        self.tip = self.root.tooltip
        self.mouse = (30, 45)
        self.target = bf.gui.Shape((100, 30)).set_position(20, 30).set_tooltip_text("A tooltip")
        self.root.add(self.target)
        self.cursor_patch = patch("pygame.mouse.set_cursor")
        self.cursor_patch.start()
        self.mouse_patch = patch.object(self.camera, "get_mouse_pos", side_effect=lambda: self.mouse)
        self.mouse_patch.start()
        self.addCleanup(self.cursor_patch.stop)
        self.addCleanup(self.mouse_patch.stop)
        self.addCleanup(bf.TimeManager().remove_register, self.scene.name)

    def advance(self, frames):
        # Exercise the real timer -> root update ordering without advancing
        # unrelated scenes left in the singleton by other tests.
        register = bf.TimeManager().registers[self.scene.name]
        for _ in range(frames):
            register.update(1 / 60)
            self.root.update(1 / 60)

    def assert_inside(self, rect, bounds):
        self.assertGreaterEqual(rect.left, bounds.left)
        self.assertGreaterEqual(rect.top, bounds.top)
        self.assertLessEqual(rect.right, bounds.right)
        self.assertLessEqual(rect.bottom, bounds.bottom)

    def test_delay_and_both_fades_can_repeat(self):
        timers = (self.tip.delay_timer, self.tip.fade_in_easer, self.tip.fade_out_easer)
        for cycle in range(3):
            with self.subTest(cycle=cycle):
                self.mouse = (30, 45)
                self.advance(45)
                self.assertTrue(self.tip.visible)
                self.assertEqual(self.tip.get_alpha(), 255)
                self.assertGreater(self.tip.rect.width, 0)
                self.mouse = (390, 230)
                self.advance(20)
                self.assertFalse(self.tip.visible)
                self.assertEqual(self.tip.get_alpha(), 0)
                for timer in timers:
                    self.assertFalse(timer.should_delete())
                    self.assertEqual(timer.register, self.scene.name)
                    self.assertIs(bf.TimeManager().registers[self.scene.name].timers[timer.uid], timer)

    def test_leaving_before_delay_finishes_cancels_appearance(self):
        self.advance(10)
        self.assertFalse(self.tip.visible)
        self.mouse = (390, 230)
        self.advance(60)
        self.assertIsNone(self.tip.target)
        self.assertTrue(self.tip.delay_timer.is_stopped)
        self.assertFalse(self.tip.visible)
        self.assertEqual(self.tip.get_alpha(), 0)

    def test_disable_and_reenable_while_pointer_stays_on_target(self):
        self.advance(45)
        self.root.set_show_tooltip(False)
        self.advance(20)
        self.assertFalse(self.tip.visible)
        self.assertIsNone(self.tip.target)
        self.root.set_show_tooltip(True)
        self.advance(45)
        self.assertTrue(self.tip.visible)
        self.assertEqual(self.tip.get_alpha(), 255)

    def test_visible_retarget_interrupts_fade_out(self):
        other = bf.gui.Shape((100, 30)).set_position(200, 30).set_tooltip_text("Another target")
        self.root.add(other)
        self.advance(45)
        self.mouse = (390, 230)
        self.advance(3)
        self.assertTrue(self.tip.visible)
        self.assertLess(self.tip.get_alpha(), 255)
        self.mouse = (210, 45)
        self.advance(10)
        self.assertIs(self.tip.target, other)
        self.assertEqual(self.tip.text, "Another target")
        self.assertTrue(self.tip.visible)
        self.assertEqual(self.tip.get_alpha(), 255)

    def test_tooltip_is_excluded_from_normal_measure_and_arrange(self):
        self.advance(45)
        with patch.object(self.tip, "measure", wraps=self.tip.measure) as measure, \
                patch.object(self.tip, "arrange", wraps=self.tip.arrange) as arrange:
            self.root.measure(self.root.rect.size)
            self.root.arrange(self.root.rect)
            measure.assert_not_called()
            arrange.assert_not_called()
            self.root.update_tree()
            measure.assert_called_once()
            arrange.assert_called_once()

    def test_new_text_is_measured_arranged_and_painted_in_same_frame(self):
        self.advance(45)
        text = "Updated content that wraps across several lines. " * 4
        self.target.set_tooltip_text(text)
        calls = []
        for widget, name, method in ((self.target, "normal", "arrange"),
                                     (self.tip, "tooltip", "measure"),
                                     (self.tip, "tooltip", "arrange"),
                                     (self.tip, "tooltip", "paint")):
            original = getattr(widget, method)

            def tracked(*args, original=original, name=name, method=method):
                calls.append((name, method, self.tip.text))
                return original(*args)

            setattr(widget, method, tracked)
        self.root.update_tree()
        self.assertEqual([(name, method) for name, method, _ in calls],
                         [("normal", "arrange"), ("tooltip", "measure"),
                          ("tooltip", "arrange"), ("tooltip", "paint")])
        self.assertTrue(all(value == text for _, _, value in calls[1:]))
        self.assertGreater(self.tip.rect.h, self.tip.font.get_height() + 4)
        self.assertLessEqual(self.tip.rect.w, 320)
        self.assertEqual(self.tip.surface.get_size(), tuple(map(int, self.tip.rect.size)))
        self.assertFalse(self.tip.dirty_surface)

    def test_measurement_does_not_change_rect_surface_alpha_or_timers(self):
        self.advance(45)
        before = (self.tip.rect.copy(), self.tip.surface, self.tip.get_alpha(),
                  self.tip.delay_timer.elapsed_time, self.tip.fade_in_easer.elapsed_time)
        self.tip.measure((100, 200))
        self.assertEqual(before, (self.tip.rect, self.tip.surface, self.tip.get_alpha(),
                                  self.tip.delay_timer.elapsed_time, self.tip.fade_in_easer.elapsed_time))

    def test_placement_flips_and_clamps_without_mutating_bounds(self):
        bounds = pygame.FRect(100, 200, 100, 100)
        before = bounds.copy()
        right_down = self.root._place_tooltip((30, 20), (105, 205), bounds, 10)
        left_up = self.root._place_tooltip((30, 20), (195, 295), bounds, 10)
        fills_viewport = self.root._place_tooltip((100, 100), (150, 250), bounds, 10)
        self.assertEqual(right_down, pygame.FRect(115, 215, 30, 20))
        self.assertEqual(left_up, pygame.FRect(155, 265, 30, 20))
        self.assertEqual(fills_viewport, bounds)
        self.assertEqual(bounds, before)

    def test_translated_camera_bounds_and_window_edges(self):
        self.camera.set_position(1000, 2000)
        self.root.set_position(1000, 2000)
        self.target.add_constraints(bf.gui.Fill())
        self.target.set_position(1000, 2000)
        self.target.set_tooltip_text("A tooltip close to the viewport edge.")
        viewport = self.camera.world_rect
        for mouse in ((1001, 2001), (1399, 2001), (1001, 2239), (1399, 2239)):
            with self.subTest(mouse=mouse):
                self.mouse = mouse
                self.advance(45)
                self.assertTrue(self.tip.visible)
                self.assert_inside(self.tip.rect, viewport.inflate(-8, -8))
                screen = self.camera.world_to_screen(self.tip.rect)
                self.assert_inside(screen, pygame.FRect(4, 4, 392, 232))

    def test_resize_rewraps_and_tiny_viewports_never_produce_negative_sizes(self):
        self.advance(45)
        self.tip.set_text("Words that must wrap into a narrow viewport. " * 6)
        for width, height in ((200, 150), (75, 80), (2, 2), (0, 0)):
            with self.subTest(size=(width, height)):
                bounds = pygame.FRect(20, 30, width, height)
                self.root._layout_tooltip(bounds.center, bounds)
                self.assert_inside(self.tip.rect, bounds)
                self.assertGreaterEqual(self.tip.rect.w, 0)
                self.assertGreaterEqual(self.tip.rect.h, 0)
                self.tip.paint_tree()

    def test_tooltip_draws_on_layer_and_does_not_intercept_hover(self):
        self.target.add_constraints(bf.gui.Fill()).set_position(0, 0)
        self.advance(45)
        self.assertIsNone(self.tip.top_at(*self.tip.rect.center))
        self.assertIs(self.root.top_at(*self.tip.rect.center), self.target)
        self.assertIn(self.tip, self.root._layers[bf.gui.GuiLayer.TOOLTIP])
        with patch.object(self.tip, "draw", wraps=self.tip.draw) as draw:
            self.root.draw(self.camera)
            draw.assert_called_once_with(self.camera)


if __name__ == "__main__":
    unittest.main()

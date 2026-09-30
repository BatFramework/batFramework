"""Viewport negotiation and interaction coverage for slider-backed scrollbars."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame
import batFramework as bf
from batFramework.gui.slider import SliderMeter


class ScrollingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((800, 600))
        bf.FontManager().init_font(None)

    def panel(self, content_size=(300, 300), size=(100, 100)):
        child = bf.gui.Shape(content_size)
        panel = bf.gui.ScrollingContainer(bf.gui.Column(), child).set_padding(0)
        panel.measure(size)
        panel.arrange(size)
        return panel

    def camera(self, panel, position):
        panel.parent_scene = Mock()
        camera = Mock()
        camera.get_mouse_pos.return_value = position
        panel.get_camera = Mock(return_value=camera)
        return camera

    def wheel(self, panel, x=0, y=-1, shift=False):
        event = pygame.Event(pygame.MOUSEWHEEL, x=x, y=y, consumed=False)
        keys = {pygame.K_LSHIFT: shift, pygame.K_RSHIFT: False}
        with patch("pygame.key.get_pressed", return_value=keys):
            panel.process_event(event)
        return event

    def test_measure_preserves_committed_geometry_scroll_and_visibility(self):
        panel = self.panel()
        panel.set_scroll((50, 70))
        panel.arrange((100, 100))
        nodes = []
        panel.visit(nodes.append)
        before = [(w.rect.copy(), w.surface, w.visible) for w in nodes]
        scroll = panel.scroll.copy()
        viewport = panel.get_inner_rect()
        panel.measure((500, 500))
        self.assertEqual(before, [(w.rect, w.surface, w.visible) for w in nodes])
        self.assertEqual(panel.scroll, scroll)
        self.assertEqual(panel.get_inner_rect(), viewport)
        panel.arrange((500, 500))
        self.assertFalse(panel.h_track.visible or panel.v_track.visible)
        self.assertEqual(panel.scroll, (0, 0))

    def test_cross_axis_bars_use_shared_viewport(self):
        panel = self.panel((96, 101))
        self.assertTrue(panel.h_track.visible and panel.v_track.visible)
        self.assertEqual(panel.get_inner_rect().size, (88, 88))
        self.assertEqual(panel.get_inner_right(), 88)
        self.assertEqual(panel.get_inner_bottom(), 88)
        self.assertEqual(panel.get_local_inner_rect(), panel.get_inner_rect())
        # Changing a visual flag must not change the layout viewport.
        panel.v_track.set_visible(False)
        self.assertEqual(panel.get_inner_width(), 88)

    def test_proportional_slider_thumbs_and_endpoints_after_resize(self):
        panel = self.panel()
        for size in ((100, 100), (180, 150), (60, 80)):
            panel.measure(size)
            panel.arrange(size)
            panel.set_scroll((999, 999))
            panel.arrange(size)
            for axis, track in enumerate((panel.h_track, panel.v_track)):
                with self.subTest(size=size, axis=axis):
                    self.assertIsInstance(track, SliderMeter)
                    rail = track.get_inner_rect()
                    expected = max(12, rail.size[axis] * panel.get_inner_rect().size[axis] / 300)
                    self.assertAlmostEqual(track.handle.rect.size[axis], expected, places=4)
                    self.assertAlmostEqual(track.handle.rect[axis] + track.handle.rect.size[axis],
                                           rail[axis] + rail.size[axis], places=4)
                    self.assertAlmostEqual(track.get_value(), 1)

    def test_slider_drag_uses_both_axes_and_clamps(self):
        panel = self.panel()
        for axis, track in enumerate((panel.h_track, panel.v_track)):
            handle = track.handle
            handle.offset = (handle.rect.w / 2, handle.rect.h / 2)
            handle.do_on_drag(handle.rect.center, track.get_inner_rect().center)
            self.assertAlmostEqual(panel.scroll[axis], 106, places=4)
            end = list(handle.rect.center)
            end[axis] = 10000
            handle.do_on_drag(handle.rect.center, end)
            self.assertAlmostEqual(panel.scroll[axis], 212)
            self.assertTrue(track.get_inner_rect().contains(handle.rect))

    def test_track_click_reuses_slider_without_taking_focus(self):
        panel = self.panel()
        track = panel.v_track
        self.camera(panel, track.get_inner_rect().center)
        panel.ask_focus = Mock()
        event = pygame.Event(pygame.MOUSEBUTTONDOWN, button=1, consumed=False)
        track.on_click_down(1, event)
        self.assertTrue(event.consumed)
        self.assertTrue(track.handle.is_dragged)
        self.assertAlmostEqual(panel.scroll.y, 106, places=4)
        panel.ask_focus.assert_not_called()

    def test_disabled_axes_reset_and_stay_at_zero(self):
        panel = self.panel()
        panel.set_scroll((60, 70))
        panel.set_scroll_x_enabled(False)
        self.assertEqual(panel.scroll, (0, 70))
        panel.set_scroll((60, 80))
        self.assertEqual(panel.scroll, (0, 80))
        panel.set_scroll_y_enabled(False)
        panel.set_scroll((60, 80))
        self.assertEqual(panel.scroll, (0, 0))
        panel.measure((100, 100))
        panel.arrange((100, 100))
        self.assertFalse(panel.h_track.visible or panel.v_track.visible)

    def test_clear_preserves_scrollbars_and_container_can_be_reused(self):
        panel = self.panel()
        tracks = (panel.h_track, panel.v_track)
        panel.set_scroll((50, 60))
        panel.clear_children()
        panel.measure((100, 100))
        panel.arrange((100, 100))
        self.assertEqual(panel.get_layout_children(), [])
        self.assertEqual(panel.children, list(tracks))
        self.assertEqual(panel.scroll, (0, 0))
        self.assertFalse(any(t.visible for t in tracks))
        panel.add(bf.gui.Shape((300, 300)))
        panel.measure((100, 100))
        panel.arrange((100, 100))
        self.assertTrue(all(t.visible for t in tracks))

    def test_smaller_final_allocation_remeasures_wrapping(self):
        label = bf.gui.Label("many words to wrap " * 20).set_auto_wraplength(True)
        panel = bf.gui.ScrollingContainer(bf.gui.Column(), label).set_padding(0)
        panel.set_scroll_x_enabled(False)
        panel.measure((300, 80))
        height = label.desired_size[1]
        panel.arrange((80, 80))
        self.assertEqual(label.available_size[0], 68)
        self.assertGreater(label.rect.h, height)
        self.assertEqual(label.rect.h, label.desired_size[1])
        self.assertEqual(panel.layout.children_rect.height, label.rect.h)

    def test_wheel_magnitude_shift_and_horizontal_events(self):
        panel = self.panel()
        self.camera(panel, panel.v_handle.rect.center)
        panel.v_handle.is_hovered = True
        self.assertTrue(self.wheel(panel, y=-3).consumed)
        self.assertEqual(panel.scroll, (0, 60))
        self.assertTrue(self.wheel(panel, y=-2, shift=True).consumed)
        self.assertEqual(panel.scroll, (40, 60))
        self.assertTrue(self.wheel(panel, x=2, y=0).consumed)
        self.assertEqual(panel.scroll, (80, 60))
        panel.set_scroll((999, 999))
        self.assertFalse(self.wheel(panel).consumed)

    def test_wheel_bubbles_to_outer_container_at_inner_boundary(self):
        inner = self.panel()
        inner.set_size((100, 100)).set_autoresize(False)
        outer = bf.gui.ScrollingContainer(bf.gui.Column(), inner, bf.gui.Shape((80, 300)))
        outer.set_padding(0)
        outer.measure((150, 150))
        outer.arrange((150, 150))
        self.camera(inner, (20, 20))
        self.camera(outer, (20, 20))
        inner.set_scroll((0, 999))
        self.assertTrue(self.wheel(outer).consumed)
        self.assertEqual(outer.scroll.y, 20)

    def test_hidden_or_outside_container_does_not_consume_wheel(self):
        panel = self.panel()
        self.camera(panel, (500, 500))
        self.assertFalse(self.wheel(panel).consumed)
        self.camera(panel, (20, 20))
        panel.set_visible(False)
        self.assertFalse(self.wheel(panel).consumed)
        self.assertIsNone(panel.top_at(*panel.v_handle.rect.center))

    def test_small_allocations_keep_thumbs_inside_rails(self):
        panel = self.panel()
        panel.set_padding((3, 5, 7, 11)).set_relief(4)
        for size in ((20, 30), (3, 3), (0, 0)):
            with self.subTest(size=size):
                panel.measure(size)
                panel.arrange((20, 30, *size))
                self.assertGreaterEqual(panel.get_inner_width(), 0)
                self.assertGreaterEqual(panel.get_inner_height(), 0)
                for track in (panel.h_track, panel.v_track):
                    rail, thumb = track.get_inner_rect(), track.handle.rect
                    self.assertGreaterEqual(thumb.left, rail.left)
                    self.assertGreaterEqual(thumb.top, rail.top)
                    self.assertLessEqual(thumb.right, rail.right)
                    self.assertLessEqual(thumb.bottom, rail.bottom)
                panel.paint_tree()

    def test_content_is_clipped_but_scrollbars_draw_in_reserved_space(self):
        panel = self.panel()
        panel.set_color("black")
        panel.get_layout_children()[0].set_color("red")
        panel.v_track.set_color("blue")
        panel.v_handle.set_color("green").set_outline_width(0)
        panel.paint_tree()
        camera = Mock()
        camera.surface = pygame.Surface((120, 120))
        camera.world_rect = pygame.FRect(0, 0, 120, 120)
        camera.world_to_screen.side_effect = lambda rect: rect.copy()
        clip = pygame.Rect(0, 0, 110, 110)
        camera.surface.set_clip(clip)
        panel.draw(camera)
        self.assertEqual(camera.surface.get_at((30, 30)), pygame.Color("red"))
        self.assertEqual(camera.surface.get_at((90, 30)), pygame.Color("black"))
        self.assertEqual(camera.surface.get_at((95, 60)), pygame.Color("blue"))
        self.assertEqual(camera.surface.get_at((95, 10)), pygame.Color("green"))
        self.assertEqual(camera.surface.get_clip(), clip)
        self.assertIs(panel.top_at(95, 10), panel.v_handle)
        panel.set_clip_children(False)
        panel.draw(camera)
        self.assertEqual(camera.surface.get_at((90, 30)), pygame.Color("red"))

    def test_regular_slider_uses_new_thumb_size_on_first_arrangement(self):
        slider = bf.gui.Slider("", default_value=.5)
        slider.measure((200, 50))
        slider.arrange((200, 50))
        meter = slider.meter
        for value in (0, .25, .75, 1):
            slider.set_value(value)
            slider.arrange((200, 50))
            self.assertAlmostEqual(meter.position_to_value(meter.handle.rect.center), value, places=5)


if __name__ == "__main__":
    unittest.main()

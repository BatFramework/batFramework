"""Exact scrollbar thumb allocations, including styled rails and changing content."""
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


class ScrollbarSizingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((800, 600))
        bf.FontManager().init_font(None)

    def panel(self, content_size):
        child = bf.gui.Shape(content_size)
        panel = bf.gui.ScrollingContainer(bf.gui.Column(), child).set_padding(0)
        return panel, child

    def layout(self, panel, size=(100, 100)):
        panel.measure(size)
        panel.arrange((30, 40, *size))

    def assert_thumb(self, track, size):
        # Check the final allocation and painted surface, not the sizing helper.
        for actual, expected in zip(track.handle.rect.size, size):
            self.assertAlmostEqual(actual, expected, delta=0.0001)
        rail, thumb = track.get_inner_rect(), track.handle.rect
        self.assertGreaterEqual(thumb.left + 0.0001, rail.left)
        self.assertGreaterEqual(thumb.top + 0.0001, rail.top)
        self.assertLessEqual(thumb.right, rail.right + 0.0001)
        self.assertLessEqual(thumb.bottom, rail.bottom + 0.0001)
        track.handle.paint_tree()
        if track.handle.visible:
            # Hidden widgets retain their old surface until shown again.
            self.assertEqual(track.handle.surface.get_size(), tuple(map(int, size)))

    def test_single_axis_proportions_and_minimum_length(self):
        # A 100px viewport showing half/quarter/tenth of the content uses
        # 50px/25px/12px thumbs: the current default minimum is 8 + 4px.
        cases = ((101, 10000 / 101), (200, 50), (400, 25),
                 (1000, 12), (100000, 12))
        for axis in (0, 1):
            for extent, length in cases:
                with self.subTest(axis=axis, content=extent):
                    content = (extent, 20) if axis == 0 else (20, extent)
                    panel, _ = self.panel(content)
                    self.layout(panel)
                    track = panel.h_track if axis == 0 else panel.v_track
                    other = panel.v_track if axis == 0 else panel.h_track
                    self.assertTrue(track.visible)
                    self.assertFalse(other.visible)
                    self.assert_thumb(track, (length, 8) if axis == 0 else (8, length))

    def test_two_axes_use_distinct_content_ratios(self):
        panel, _ = self.panel((200, 400))
        self.layout(panel)
        self.assertEqual(panel.get_inner_rect().size, (88, 88))
        # Both rails are 88px long: x shows 88/200, y shows 88/400.
        self.assert_thumb(panel.h_track, (38.72, 8))
        self.assert_thumb(panel.v_track, (8, 19.36))

    def test_container_padding_and_relief_are_excluded_from_viewport(self):
        panel, _ = self.panel((376, 752))
        panel.set_padding((5, 7, 11, 13)).set_relief(3)
        self.layout(panel, (216, 223))
        # 200x200 inside the decoration, 188x188 after scrollbar reservations.
        self.assertEqual(panel.get_inner_rect(), pygame.FRect(35, 47, 188, 188))
        self.assert_thumb(panel.h_track, (94, 8))
        self.assert_thumb(panel.v_track, (8, 47))

    def test_track_padding_and_relief_use_inner_rail_length(self):
        panel, _ = self.panel((352, 704))
        panel.set_scrollbar_thickness(20)
        for track in (panel.h_track, panel.v_track):
            track.set_padding((2, 3, 4, 5)).set_relief(2)
        self.layout(panel, (200, 200))
        self.assertEqual(panel.get_inner_rect().size, (176, 176))
        self.assertEqual(panel.h_track.get_inner_rect().size, (170, 10))
        self.assertEqual(panel.v_track.get_inner_rect().size, (14, 166))
        # Content fractions are 1/2 and 1/4; rail padding is applied only once.
        self.assert_thumb(panel.h_track, (85, 10))
        self.assert_thumb(panel.v_track, (14, 41.5))

    def test_custom_thickness_gaps_and_short_rails_bound_minimum(self):
        panel, _ = self.panel((1000, 1000))
        panel.set_scrollbar_thickness(10).set_scrollbar_x_gap(3).set_scrollbar_y_gap(7)
        self.layout(panel)
        self.assertEqual(panel.get_inner_rect().size, (83, 87))
        self.assert_thumb(panel.h_track, (13, 10))
        self.assert_thumb(panel.v_track, (10, 17))
        # The preferred minima exceed these rails, so the rail is authoritative.
        self.layout(panel, (25, 25))
        self.assert_thumb(panel.h_track, (8, 10))
        self.assert_thumb(panel.v_track, (10, 12))
        self.layout(panel, (0, 0))
        self.assert_thumb(panel.h_track, (0, 0))
        self.assert_thumb(panel.v_track, (0, 0))

    def test_thumb_constraints_are_bounded_by_rail(self):
        panel, _ = self.panel((200, 400))
        panel.h_handle.add_constraints(bf.gui.MinWidth(60), bf.gui.MaxHeight(4))
        panel.v_handle.add_constraints(bf.gui.MinHeight(30), bf.gui.MaxWidth(5))
        self.layout(panel)
        self.assert_thumb(panel.h_track, (60, 4))
        self.assert_thumb(panel.v_track, (5, 30))
        self.layout(panel, (30, 30))
        self.assert_thumb(panel.h_track, (18, 4))
        self.assert_thumb(panel.v_track, (5, 18))

    def test_content_changes_recompute_both_thumbs_in_one_pass(self):
        panel, child = self.panel((20, 200))
        for width, length, horizontal_visible in ((20, 50, False), (90, 38.72, True),
                                                   (20, 50, False)):
            with self.subTest(width=width):
                child.set_size((width, 200))
                self.layout(panel)
                self.assertEqual(panel.h_track.visible, horizontal_visible)
                self.assert_thumb(panel.v_track, (8, length))
        child.set_size((20, 100))
        self.layout(panel)
        self.assertFalse(panel.h_track.visible or panel.v_track.visible)
        self.assert_thumb(panel.h_track, (0, 0))
        self.assert_thumb(panel.v_track, (0, 0))
        child.set_size((20, 400))
        self.layout(panel)
        self.assertTrue(panel.v_track.visible)
        self.assert_thumb(panel.v_track, (8, 25))

    def test_layout_gaps_and_child_removal_change_content_extent(self):
        children = [bf.gui.Shape((20, 40)) for _ in range(3)]
        panel = bf.gui.ScrollingContainer(bf.gui.Column(10), *children).set_padding(0)
        self.layout(panel)
        self.assertEqual(panel.layout.children_rect.height, 140)
        self.assert_thumb(panel.v_track, (8, 10000 / 140))
        panel.remove(children[-1])
        self.layout(panel)
        self.assertFalse(panel.v_track.visible)
        self.assert_thumb(panel.v_track, (0, 0))
        panel.add(children[-1])
        self.layout(panel)
        self.assert_thumb(panel.v_track, (8, 10000 / 140))

    def test_final_allocation_updates_size_and_position_without_second_arrange(self):
        panel, _ = self.panel((20, 400))
        self.layout(panel)
        panel.set_scroll((0, 100))
        # Measure the old offer, then assign a different final height. Thumb
        # centers must be calculated using the new thumb length immediately.
        panel.measure((100, 100))
        panel.arrange((30, 40, 100, 200))
        self.assert_thumb(panel.v_track, (8, 100))
        self.assertAlmostEqual(panel.v_handle.rect.top, 90)
        panel.measure((100, 200))
        panel.arrange((30, 40, 100, 80))
        self.assert_thumb(panel.v_track, (8, 16))
        self.assertAlmostEqual(panel.v_handle.rect.top, 60)

    def test_scroll_changes_position_without_changing_thumb_size(self):
        panel, _ = self.panel((200, 400))
        self.layout(panel)
        for fraction in (0, .25, .5, 1):
            panel.set_scroll((112 * fraction, 312 * fraction))
            panel.arrange((30, 40, 100, 100))
            self.assert_thumb(panel.h_track, (38.72, 8))
            self.assert_thumb(panel.v_track, (8, 19.36))
            self.assertAlmostEqual(panel.h_handle.rect.left, 30 + 49.28 * fraction, places=4)
            self.assertAlmostEqual(panel.v_handle.rect.top, 40 + 68.64 * fraction, places=4)

    def test_scene_updates_draw_handles_and_include_their_debug_rectangles(self):
        scene = bf.Scene("scrollbar-sizing-visibility")
        panel, _ = self.panel((200, 400))
        panel.set_size((100, 100)).set_autoresize(False)
        for track in (panel.h_track, panel.v_track):
            track.set_color("blue")
            track.handle.set_color("green").set_outline_width(0)
        scene.root.add(panel)
        scene.flush_entity_changes()
        target = pygame.Surface((800, 600))
        with patch.object(scene.hud_camera, "get_mouse_pos", return_value=(700, 500)), \
                patch("pygame.mouse.set_cursor"), \
                patch.object(bf.Context, "debug_mode", bf.debugMode.HIDDEN):
            for frame in range(3):
                with self.subTest(frame=frame):
                    scene.update(1 / 60)
                    scene.draw(target)
                    self.assert_thumb(panel.h_track, (38.72, 8))
                    self.assert_thumb(panel.v_track, (8, 19.36))
                    for track in (panel.h_track, panel.v_track):
                        handle = track.handle
                        self.assertTrue(handle.visible)
                        self.assertIn((handle.rect, handle.debug_color),
                                      list(scene.root.get_debug_outlines()))
                        center = scene.hud_camera.world_to_screen(handle.rect).center
                        self.assertEqual(target.get_at(tuple(map(int, center))), pygame.Color("green"))
            with patch.object(bf.Context, "debug_mode", bf.debugMode.OUTLINES):
                scene.draw(target)
                for axis, track in enumerate((panel.h_track, panel.v_track)):
                    rect = pygame.Rect(scene.hud_camera.world_to_screen(track.handle.rect))
                    point = (rect.right - 1, rect.centery) if axis == 0 else (rect.centerx, rect.bottom - 1)
                    self.assertEqual(target.get_at(point), pygame.Color(track.handle.debug_color))


if __name__ == "__main__":
    unittest.main()

"""Natural option measurement, anchored popup allocation, and interaction."""
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


class DropdownTestStyle(bf.gui.Style):
    def apply(self, widget):
        if isinstance(widget, bf.gui.Button):
            widget.set_padding((8, 5)).set_color("navy")


class DropdownTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((400, 300))
        bf.FontManager().init_font(None)

    def setUp(self):
        # Keep this theme and its widget registrations local to each test.
        manager = bf.gui.StyleManager()
        for name, value in (("styles", list(manager.styles)), ("widgets", set()), ("lookup", {})):
            state = patch.object(manager, name, value)
            state.start()
            self.addCleanup(state.stop)
        manager.add(DropdownTestStyle())
        self.scene = bf.Scene(self.id())
        self.scene.flush_entity_changes()
        self.root = self.scene.root
        self.camera = self.scene.hud_camera
        self.camera.set_size((400, 300)).set_position(0, 0)
        self.root.set_size((400, 300), force=True)
        self.mouse = (399, 299)
        cursor = patch("pygame.mouse.set_cursor")
        mouse = patch.object(self.camera, "get_mouse_pos", side_effect=lambda: self.mouse)
        cursor.start()
        mouse.start()
        self.addCleanup(cursor.stop)
        self.addCleanup(mouse.stop)
        self.addCleanup(bf.TimeManager().remove_register, self.scene.name)
        self.dropdown = bf.gui.Dropdown(["Balanced", "Fast", "Precise"])
        self.dropdown.set_size((180, 28)).set_autoresize(False).set_position(30, 40)
        self.root.add(self.dropdown)

    def open(self):
        self.dropdown.open()
        self.root.update_tree()
        return self.dropdown.panel

    def assert_inside(self, rect, bounds):
        self.assertGreaterEqual(rect.left, bounds.left)
        self.assertGreaterEqual(rect.top, bounds.top)
        self.assertLessEqual(rect.right, bounds.right)
        self.assertLessEqual(rect.bottom, bounds.bottom)

    def test_natural_measurement_does_not_request_window_width(self):
        panel = self.dropdown.panel
        before = panel.rect.copy()
        desired = panel.measure((400, 300))
        self.assertLess(desired[0], 180)
        self.assertEqual(panel.rect, before)
        panel = self.open()
        self.assertEqual(panel.rect.width, 180)
        self.assertEqual(panel.rect.topleft, (30, 72))
        for row in panel.get_layout_children():
            self.assertEqual(row.rect.left, panel.get_inner_rect().left)
            self.assertEqual(row.rect.width, panel.get_inner_width())
            self.assert_inside(row.text_rect, row.get_local_inner_rect())

    def test_wider_options_expand_panel_but_respect_viewport(self):
        self.dropdown.set_options(["A much wider option than the small trigger"])
        self.dropdown.set_size((50, 28))
        panel = self.open()
        self.assertGreater(panel.rect.width, 50)
        self.assertLessEqual(panel.rect.width, 392)
        self.assert_inside(panel.rect, self.camera.world_rect.inflate(-8, -8))

    def test_flips_above_and_clamps_at_right_edge(self):
        self.dropdown.set_position(350, 260)
        panel = self.open()
        self.assertEqual(panel.rect.bottom, self.dropdown.rect.top - 4)
        self.assertEqual(panel.rect.right, 396)
        self.assert_inside(panel.rect, self.camera.world_rect.inflate(-8, -8))

    def test_long_list_scrolls_on_side_with_more_space(self):
        self.dropdown.set_options([f"Option {i}" for i in range(50)])
        self.dropdown.set_position(30, 100)
        panel = self.open()
        self.assertIsInstance(panel, bf.gui.ScrollingContainer)
        self.assertEqual(panel.rect.top, 132)
        self.assertEqual(panel.rect.bottom, 296)
        self.assertTrue(panel.v_track.visible)
        self.assertFalse(panel.h_track.visible)
        self.assertGreater(panel.layout.children_rect.height, panel.get_inner_height())
        self.dropdown.set_by_index(49)
        self.root.update_tree()
        selected = self.dropdown._option_buttons[49]
        self.assert_inside(selected.rect, panel.get_inner_rect())
        self.assertGreater(panel.scroll.y, 0)
        self.assertAlmostEqual(panel.v_handle.rect.bottom, panel.v_track.get_inner_rect().bottom, places=4)

    def test_selected_row_is_visible_on_first_open(self):
        self.dropdown.set_options([f"Option {i}" for i in range(40)])
        self.dropdown.set_by_index(30)
        panel = self.open()
        self.assert_inside(self.dropdown._option_buttons[30].rect, panel.get_inner_rect())

    def test_panel_maximum_height_and_wrapped_options(self):
        self.dropdown.set_options(["Long option with words to wrap " * 8 for _ in range(8)])
        self.dropdown.panel_max_height = 90
        panel = self.open()
        self.assertEqual(panel.rect.height, 90)
        self.assertTrue(panel.v_track.visible)
        row = panel.get_layout_children()[0]
        self.assertGreater(row.rect.height, row.font.get_height() + 10)
        self.assertLessEqual(row.rect.width, panel.get_inner_width())

    def test_root_arranges_anchor_before_popup_once_per_update(self):
        panel = self.open()
        calls = []
        nodes = [self.dropdown, panel, *panel.get_layout_children()]
        for widget in nodes:
            original = widget.arrange

            def tracked(rect, widget=widget, original=original):
                calls.append(widget)
                original(rect)

            widget.arrange = tracked
        self.dropdown.set_size((230, 28)).set_position(100, 200)
        self.root.update_tree()
        self.assertEqual(calls, nodes)
        self.assertEqual(panel.rect.width, 230)
        self.assertEqual(panel.rect.left, 100)
        self.assert_inside(panel.rect, self.camera.world_rect.inflate(-8, -8))

    def test_translated_camera_and_small_viewport(self):
        self.camera.set_position(1000, 2000)
        self.root.set_position(1000, 2000)
        self.dropdown.set_position(1350, 2260)
        panel = self.open()
        self.assert_inside(panel.rect, self.camera.world_rect.inflate(-8, -8))
        for size in ((60, 45), (2, 2), (0, 0)):
            with self.subTest(size=size):
                bounds = pygame.FRect(1000, 2000, *size)
                panel.layout_popup(bounds)
                self.assert_inside(panel.rect, bounds)
                panel.paint_tree()

    def test_popup_hit_testing_wins_over_later_normal_children(self):
        panel = self.open()
        blocker = bf.gui.Shape((400, 300))
        self.root.add(blocker)
        row = panel.get_layout_children()[1]
        self.assertIs(self.root.top_at(*row.rect.center), row)

    def test_selection_closes_panel_and_updates_binding(self):
        panel = self.open()
        panel.get_layout_children()[1].click()
        self.assertEqual(self.dropdown.value_var.value, "Fast")
        self.assertFalse(self.dropdown.is_open)
        self.assertNotIn(panel, self.root.children)
        self.assertNotIn(panel, self.root._popup_layouts)

    def test_keyboard_selection_escape_and_outside_click(self):
        panel = self.open()
        row = panel.get_layout_children()[2]
        event = pygame.Event(pygame.KEYDOWN, key=pygame.K_RETURN, consumed=False)
        row.on_key_down(event.key, event)
        self.assertEqual(self.dropdown.get_current_value(), "Precise")
        self.assertTrue(event.consumed)
        self.open()
        event = pygame.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, consumed=False)
        panel.handle_event(event)
        self.assertFalse(self.dropdown.is_open)
        self.assertTrue(event.consumed)
        self.open()
        self.mouse = (399, 299)
        panel.handle_event(pygame.Event(pygame.MOUSEBUTTONDOWN, button=1, consumed=False))
        self.assertFalse(self.dropdown.is_open)

    def test_option_styling_exists_before_scene_attachment_and_for_new_rows(self):
        unattached = bf.gui.Dropdown(["A", "B"])
        self.assertEqual(len(unattached.panel.get_layout_children()), 2)
        for row in unattached.panel.get_layout_children():
            self.assertEqual(row.color, "navy")
            self.assertEqual(row.padding, (8, 5, 8, 5))
        self.open()
        self.dropdown.set_options(["A", "B", "C", "D", "E"])
        self.root.update_tree()
        for row in self.dropdown.panel.get_layout_children():
            self.assertEqual(row.color, "navy")
            self.assertEqual(row.padding, (8, 5, 8, 5))

    def test_registered_style_reapplies_to_detached_and_new_options(self):
        class UpdatedStyle(bf.gui.Style):
            def apply(self, widget):
                if isinstance(widget, bf.gui.Button):
                    widget.set_color("purple")

        self.open()
        self.dropdown.close()
        bf.gui.StyleManager().add(UpdatedStyle())
        self.dropdown.set_options(["A", "B", "C", "D"])
        for row in self.dropdown.panel.get_layout_children():
            self.assertEqual(row.color, "purple")
        self.open()
        bf.gui.StyleManager().update_forced()
        for row in self.dropdown.panel.get_layout_children():
            self.assertEqual(row.color, "purple")

    def test_empty_options_close_panel_and_can_be_repopulated(self):
        panel = self.open()
        self.dropdown.set_options([], reset_index=False)
        self.assertFalse(self.dropdown.is_open)
        self.assertIsNone(self.dropdown.current_index)
        self.dropdown.open()
        self.assertFalse(self.dropdown.is_open)
        self.dropdown.set_options(["New"], reset_index=False)
        self.assertIs(self.open(), panel)
        self.assertEqual(self.dropdown.get_current_index(), 0)

    def test_removing_owner_detaches_open_popup(self):
        panel = self.open()
        self.root.remove(self.dropdown)
        self.assertFalse(self.dropdown.is_open)
        self.assertNotIn(panel, self.root.children)
        self.assertNotIn(panel, self.root._popup_layouts)


if __name__ == "__main__":
    unittest.main()

"""Regression coverage for the measure, arrange, and paint lifecycle."""
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame
import batFramework as bf


class CountingLabel(bf.gui.Label):
    def __init__(self, text="Text"):
        super().__init__(text)
        self.paint_count = 0

    def paint(self):
        self.paint_count += 1
        super().paint()


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((800, 600))
        bf.FontManager().init_font(None)

    def test_static_labels_only_repaint_when_invalidated(self):
        label = CountingLabel()
        label.measure((200, 100))
        label.arrange(label.desired_size)
        self.assertEqual(label.paint_count, 0)
        label.paint_tree()
        label.arrange(label.desired_size)
        label.paint_tree()
        self.assertEqual(label.paint_count, 1)
        label.set_text_color("red")
        label.paint_tree()
        self.assertEqual(label.paint_count, 2)

    def test_dynamic_renderer_repaints_even_when_surface_is_clean(self):
        label = CountingLabel()
        label.measure((200, 100))
        label.arrange(label.desired_size)
        label.paint_tree()
        label.renderer.DYNAMIC = True
        for _ in range(3):
            self.assertFalse(label.dirty_surface)
            label.paint_tree()
        self.assertEqual(label.paint_count, 4)
        label.hide()
        label.paint_tree()
        self.assertEqual(label.paint_count, 4)
        label.show()
        label.paint_tree()
        self.assertEqual(label.paint_count, 5)

    def test_dynamic_text_effect_controls_repainting(self):
        class Effect(bf.gui.textEffects.TextEffect):
            DYNAMIC = True

            def apply(self, text):
                return text

        label = CountingLabel().set_text_effect(Effect())
        label.measure((200, 100))
        label.arrange(label.desired_size)
        label.paint_tree()
        label.paint_tree()
        self.assertEqual(label.paint_count, 2)
        label.set_text_effect(None)
        label.paint_tree()
        label.paint_tree()
        self.assertEqual(label.paint_count, 3)

    def test_cursor_scroll_is_ready_before_paint(self):
        entry = bf.gui.TextInput("abcdefghijklmnopqrstuvwxyz").set_size((50, 30)).set_autoresize(False)
        entry.set_cursor_position(26, 0)
        entry.measure((50, 30))
        entry.arrange((50, 30))
        self.assertFalse(entry.edited_this_frame)
        self.assertGreater(entry.text_scroll.x, 0)
        cx, _, _ = entry._get_cursor_pixel_rect()
        self.assertLessEqual(cx - entry.text_scroll.x, entry.get_inner_width())
        scroll_at_paint = []
        paint = entry.paint
        entry.paint = lambda: (scroll_at_paint.append(entry.text_scroll.x), paint())
        entry.paint_tree()
        self.assertEqual(scroll_at_paint, [entry.text_scroll.x])

    def test_cursor_scroll_moves_all_siblings_in_same_arrangement(self):
        entry = bf.gui.TextInput("abcdefghijklmnopqrstuvwxyz")
        sibling = bf.gui.Shape((20, 20))
        panel = bf.gui.ScrollingContainer(bf.gui.Row(), sibling, entry)
        panel.set_padding(0).set_size((100, 50)).set_autoresize(False)
        entry.set_cursor_position(26, 0)
        panel.measure((100, 50))
        panel.arrange((100, 50))
        self.assertGreater(panel.scroll.x, 0)
        self.assertEqual(sibling.rect.x, -panel.scroll.x)
        self.assertEqual(entry.rect.x, sibling.rect.right)
        cx, _, _ = entry._get_cursor_pixel_rect()
        caret_x = entry.get_inner_left() + cx - entry.text_scroll.x
        self.assertLessEqual(caret_x, panel.get_inner_rect().right)

    def test_each_composite_child_is_arranged_once(self):
        controls = [bf.gui.Slider("Volume"), bf.gui.Toggle("Enabled"),
                    bf.gui.Selector("Mode", ["a", "b"]), bf.gui.TextInput("Text"),
                    bf.gui.Dropdown(["a", "b"]), bf.gui.CollapseContainer("More"),
                    bf.gui.ScrollingContainer(bf.gui.Column(), bf.gui.Shape((300, 300)))]
        for control in controls:
            with self.subTest(control=type(control).__name__):
                extra = bf.gui.Shape((3, 3))
                control.add(extra)
                nodes = []
                control.visit(nodes.append)
                counts = {node: 0 for node in nodes}
                for node in nodes:
                    original = node.arrange

                    def tracked(rect, node=node, original=original):
                        counts[node] += 1
                        original(rect)

                    node.arrange = tracked
                control.measure((200, 100))
                control.arrange((200, 100))
                self.assertEqual(list(counts.values()), [1] * len(nodes))

    def test_root_traverses_children_without_painting_itself(self):
        root = bf.gui.Root()
        root.visible = True
        root.paint = Mock(side_effect=AssertionError("Root surface should not paint"))
        label = CountingLabel()
        root.add(label)
        root.update_tree()
        root.paint.assert_not_called()
        self.assertEqual(label.paint_count, 1)

    def test_scene_entry_uses_new_tree_pipeline(self):
        root = Mock(spec=bf.gui.Root)
        scene = SimpleNamespace(root=root, name="test", do_on_enter=Mock())
        with patch.object(bf, "TimeManager"):
            bf.Scene.on_enter(scene)
        root.update_tree.assert_called_once_with()
        scene.do_on_enter.assert_called_once_with()

    def test_dropdown_panel_positions_children_after_final_placement(self):
        dropdown = bf.gui.Dropdown(["a", "b"])
        dropdown._populate_panel()
        dropdown.measure((200, 100))
        dropdown.arrange((20, 30, 100, 25))
        panel = dropdown._panel
        panel.layout_popup(pygame.FRect(0, 0, 200, 200))
        self.assertEqual(panel.rect.topleft, (dropdown.rect.left, dropdown.rect.bottom + dropdown.panel_gap))
        self.assertEqual(panel.get_layout_children()[0].rect.top, panel.get_inner_rect().top)

    def test_removed_api_is_not_exposed(self):
        for name in ("apply_pre_updates", "apply_post_updates", "apply_updates",
                     "resolve_constraints", "resolve_size", "build",
                     "find_highest_dirty_constraints_widget"):
            for cls in (bf.gui.Widget, bf.gui.Root, bf.gui.Label, bf.gui.TextInput,
                        bf.gui.Container, bf.gui.Slider, bf.gui.Toggle, bf.gui.Selector):
                self.assertFalse(hasattr(cls, name), f"{cls.__name__}.{name}")
        for name in ("apply", "apply_constraint", "evaluate", "on_removal"):
            self.assertFalse(hasattr(bf.gui.Constraint, name))


if __name__ == "__main__":
    unittest.main()

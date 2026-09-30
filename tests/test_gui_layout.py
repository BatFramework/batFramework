"""Headless regression tests for the measure/arrange contract.

Run with: python -m unittest discover -s tests -v
"""
import os
from pathlib import Path
import sys
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame
import batFramework as bf


class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((800, 600))
        bf.FontManager().init_font(None)

    def setUp(self):
        self.root = bf.gui.Root()

    def box(self, width, height):
        return bf.gui.Shape((width, height))

    def container(self, layout, *children):
        return bf.gui.Container(layout, *children).set_padding(0)

    def update(self, *children):
        self.root.add(*children)
        self.root.update_tree()

    def test_measure_does_not_change_geometry_or_surface(self):
        slider = bf.gui.Slider("Volume")
        panel = self.container(bf.gui.Column(), slider).add_constraints(bf.gui.Width(200))
        self.root.add(panel)
        nodes = []
        self.root.visit(nodes.append)
        before = [(w.rect.copy(), w.surface, w.autoresize_w, w.autoresize_h) for w in nodes]
        self.root.measure((800, 600))
        self.assertEqual(slider.available_size, (200, 600))
        self.assertEqual(before, [(w.rect, w.surface, w.autoresize_w, w.autoresize_h) for w in nodes])

    def test_deep_tree_finishes_in_one_update(self):
        child = self.box(27, 19)
        top = child
        for _ in range(15):
            top = self.container(bf.gui.Column(), top).set_padding(2)
        self.update(top)
        self.assertEqual(top.rect.size, (87, 79))
        self.assertEqual(child.rect.topleft, (30, 30))
        child.set_size((50, 10))
        self.root.update_tree()
        self.assertEqual(top.rect.size, (110, 70))

    def test_parent_assignment_is_authoritative(self):
        label = bf.gui.Label("long text").set_min_size((100, 100))
        label.measure((20, 10))
        self.assertEqual(label.desired_size, (20, 10))
        label.arrange((7, 9, 12, 5))
        self.assertEqual(label.rect, pygame.FRect(7, 9, 12, 5))

    def test_fixed_request_recovers_after_shrink(self):
        box = self.box(200, 40).set_autoresize(False)
        self.root.add(box)
        for width in (50, 300, 10, 400):
            self.root.set_size((width, 100), force=True)
            self.root.update_tree()
            self.assertEqual(box.rect.size, (min(200, width), 40))

    def test_asymmetric_padding_and_relief(self):
        child = self.box(20, 10)
        panel = self.container(bf.gui.Column(), child).set_padding((3, 5, 7, 11)).set_relief(4)
        self.update(panel)
        self.assertEqual(panel.rect.size, (30, 30))
        self.assertEqual(child.rect, pygame.FRect(3, 5, 20, 10))

    def test_fill_and_percentage_use_new_parent_size(self):
        child = self.box(10, 10).add_constraints(bf.gui.PercentageWidth(.5), bf.gui.FillY())
        panel = self.container(bf.gui.FreeLayout(), child).add_constraints(bf.gui.Fill())
        self.update(panel)
        self.assertEqual(child.rect.size, (400, 600))
        self.root.set_size((240, 80), force=True)
        self.root.update_tree()
        self.assertEqual(child.rect.size, (120, 80))

    def test_priorities_are_deterministic(self):
        child = self.box(10, 10).add_constraints(bf.gui.Width(200).set_priority(5), bf.gui.FillX())
        self.update(child)
        self.assertEqual(child.rect.w, 200)
        next(c for c in child.constraints if c.name == "FillX").set_priority(10)
        self.root.update_tree()
        self.assertEqual(child.rect.w, 800)

    def test_remove_constraint_restores_intrinsic_request(self):
        child = self.box(40, 10).add_constraints(bf.gui.FillX())
        self.update(child)
        child.remove_constraints("FillX")
        self.root.update_tree()
        self.assertEqual(child.rect.w, 40)
        self.assertTrue(child.autoresize_w)

    def test_weighted_grow_is_parent_owned(self):
        fixed = self.box(40, 20)
        a = self.box(5, 20).add_constraints(bf.gui.GrowH(1))
        b = self.box(5, 20).add_constraints(bf.gui.GrowH(2))
        row = self.container(bf.gui.Row(10), fixed, a, b).add_constraints(bf.gui.Width(300))
        self.update(row)
        self.assertEqual(fixed.rect.w, 40)
        self.assertEqual(a.rect.w, 80)
        self.assertEqual(b.rect.w, 160)
        self.assertEqual(b.rect.right, row.rect.right)
        self.assertTrue(a.autoresize_w)

    def test_grow_reacts_to_changed_fixed_sibling(self):
        fixed = self.box(30, 10)
        growing = self.box(1, 10).add_constraints(bf.gui.GrowH())
        row = self.container(bf.gui.Row(), fixed, growing).add_constraints(bf.gui.Width(200))
        self.update(row)
        fixed.set_size((90, 10))
        self.root.update_tree()
        self.assertEqual(growing.rect.w, 110)

    def test_row_fill_arranges_nested_descendants(self):
        children = [self.container(bf.gui.Column(), self.box(5, 10).add_constraints(bf.gui.FillX())) for _ in range(2)]
        panel = self.container(bf.gui.RowFill(10), *children).add_constraints(bf.gui.Width(210))
        self.update(panel)
        for child in children:
            self.assertEqual(child.rect.w, 100)
            self.assertEqual(child.children[0].rect.w, 100)

    def test_grid_fill(self):
        children = [self.box(10, 10) for _ in range(4)]
        panel = self.container(bf.gui.GridFill(2, 2, 10), *children).add_constraints(bf.gui.Width(210), bf.gui.Height(110))
        self.update(panel)
        self.assertEqual(children[-1].rect, pygame.FRect(110, 60, 100, 50))

    def test_anchors_follow_final_sizes(self):
        panel = self.container(bf.gui.Column(), self.box(80, 30)).add_constraints(bf.gui.AnchorBottomRight())
        self.update(panel)
        self.assertEqual(panel.rect.bottomright, (800, 600))
        self.assertEqual(panel.children[0].rect.topleft, panel.rect.topleft)

    def test_text_change_resizes_parent_same_frame(self):
        label = bf.gui.Label("a")
        panel = self.container(bf.gui.Column(), label)
        self.update(panel)
        previous = panel.rect.w
        label.set_text("a much longer label")
        self.root.update_tree()
        self.assertGreater(panel.rect.w, previous)
        self.assertEqual(panel.rect.w, label.rect.w)

    def test_auto_wrap_uses_offered_width(self):
        label = bf.gui.Label("some words to wrap over several lines").set_auto_wraplength(True)
        label.measure((80, 600))
        narrow = label.desired_size
        label.measure((400, 600))
        self.assertGreater(narrow[1], label.desired_size[1])

    def test_image_reports_intrinsic_size_and_obeys_allocation(self):
        image = bf.gui.Image().from_surface(pygame.Surface((70, 30))).set_padding(2)
        self.assertEqual(image.measure((800, 600)), (74, 34))
        image.arrange((10, 10))
        image.paint_tree()
        self.assertEqual(image.rect.size, (10, 10))

    def test_scrolling_retains_content_extent(self):
        children = [self.box(80, 40) for _ in range(5)]
        panel = bf.gui.ScrollingContainer(bf.gui.Column(), *children).set_padding(0)
        panel.add_constraints(bf.gui.Width(100), bf.gui.Height(100))
        self.update(panel)
        self.assertEqual(panel.layout.children_rect.h, 200)
        self.assertTrue(panel.v_track.visible)
        self.assertFalse(panel.h_track.visible)
        panel.set_scroll((0, 100))
        self.root.update_tree()
        self.assertEqual(children[0].rect.y, -100)
        self.assertEqual(children[-1].rect.bottom, 100)

    def test_horizontal_scroll_track_has_correct_geometry(self):
        panel = bf.gui.ScrollingContainer(bf.gui.Row(), self.box(200, 20)).set_padding(0)
        panel.add_constraints(bf.gui.Width(100), bf.gui.Height(80))
        self.update(panel)
        self.assertTrue(panel.h_track.visible)
        self.assertEqual(panel.h_track.rect.size, (100, 8))
        self.assertEqual(panel.h_track.rect.bottom, 80)

    def test_scrollbars_disappear_after_content_removed(self):
        child = self.box(300, 300)
        panel = bf.gui.ScrollingContainer(bf.gui.Column(), child).set_padding(0)
        panel.add_constraints(bf.gui.Width(100), bf.gui.Height(100))
        self.update(panel)
        panel.remove(child)
        self.root.update_tree()
        self.assertFalse(panel.v_track.visible or panel.h_track.visible)
        self.assertEqual(panel.layout.children_rect.size, (0, 0))

    def test_composites_arrange_from_final_allocation(self):
        widgets = [bf.gui.Slider("Volume"), bf.gui.Toggle("Enabled"),
                   bf.gui.TextInput("Hello"), bf.gui.Dropdown(["a", "b"]),
                   bf.gui.CollapseContainer("More", bf.gui.Column(), self.box(40, 20))]
        for widget in widgets:
            with self.subTest(widget=type(widget).__name__):
                widget.measure((200, 100))
                widget.arrange((20, 30, 200, 100))
                widget.paint_tree()
                self.assertEqual(widget.rect, pygame.FRect(20, 30, 200, 100))
                self.assertEqual(widget.surface.get_size(), (200, 100))

    def test_repeated_updates_are_stable(self):
        panel = self.container(bf.gui.Column(3), bf.gui.Slider("Volume"), bf.gui.Toggle("On"))
        self.update(panel)
        nodes = []
        self.root.visit(nodes.append)
        before = [w.rect.copy() for w in nodes]
        for _ in range(5):
            self.root.update_tree()
        self.assertEqual(before, [w.rect for w in nodes])

    def test_zero_and_invalid_offers(self):
        widget = self.box(10, 10).set_padding(10)
        self.assertEqual(widget.measure((0, 0)), (0, 0))
        widget.arrange((0, 0))
        self.assertEqual(widget.get_inner_rect().size, (0, 0))
        for size in [(-1, 10), (float("nan"), 10)]:
            with self.assertRaises(ValueError):
                widget.measure(size)
        with self.assertRaises(ValueError):
            widget.arrange((float("inf"), 10))

    def test_custom_size_constraint_is_pure(self):
        class HalfHeight(bf.gui.Constraint):
            def __init__(self):
                super().__init__()
                self.affects_size = True

            def constrain_size(self, child, preferred, available):
                return preferred[0], available[1] / 2

        child = self.box(30, 10).add_constraints(HalfHeight())
        self.assertEqual(child.measure((200, 100)), (30, 50))
        self.assertEqual(child.rect.size, (30, 10))

    def test_shared_constraint_removal_is_independent(self):
        shared = bf.gui.FillX()
        a = self.box(30, 10).add_constraints(shared)
        b = self.box(40, 10).set_autoresize(False).add_constraints(shared)
        self.update(a, b)
        a.remove_constraints("FillX")
        b.remove_constraints("FillX")
        self.root.update_tree()
        self.assertEqual(a.rect.w, 30)
        self.assertEqual(b.rect.w, 40)
        self.assertTrue(a.autoresize_w)
        self.assertFalse(b.autoresize_w)

    def test_min_max_and_aspect_ratio(self):
        child = self.box(80, 20).add_constraints(bf.gui.MaxWidth(50), bf.gui.MinHeight(40))
        self.assertEqual(child.measure((800, 600)), (50, 40))
        child.remove_constraints("MaxWidth", "MinHeight")
        child.add_constraints(bf.gui.AspectRatio(.5))
        self.assertEqual(child.measure((60, 20)), (40, 20))

    def test_grow_obeys_maximum(self):
        child = self.box(10, 10).add_constraints(bf.gui.GrowH(), bf.gui.MaxWidth(50))
        panel = self.container(bf.gui.Row(), child).add_constraints(bf.gui.Width(200))
        self.update(panel)
        self.assertEqual(child.rect.w, 50)

    def test_layout_constraint_replacement(self):
        child = self.box(10, 10)
        layout = bf.gui.Column().set_child_constraints(bf.gui.FillX())
        panel = self.container(layout, child).add_constraints(bf.gui.Width(200))
        self.update(panel)
        layout.set_child_constraints(bf.gui.Width(40))
        self.root.update_tree()
        self.assertEqual(child.rect.w, 40)
        self.assertFalse(child.has_constraint("FillX"))

    def test_wrapping_accounts_for_vertical_scrollbar(self):
        child = bf.gui.Label("many words to wrap " * 20).set_auto_wraplength(True)
        panel = bf.gui.ScrollingContainer(bf.gui.Column(), child).set_padding(0)
        panel.set_scroll_x_enabled(False).add_constraints(bf.gui.Width(100), bf.gui.Height(50))
        self.update(panel)
        self.assertTrue(panel.v_track.visible)
        self.assertEqual(child.available_size[0], panel.get_inner_width())
        self.assertEqual(child.rect.h, child.get_min_required_size()[1])

    def test_collapse_expands_and_collapses_in_one_update(self):
        collapse = bf.gui.CollapseContainer("More", bf.gui.Column(), self.box(80, 50))
        self.update(collapse)
        height = collapse.rect.h
        collapse.state.value = True
        self.root.update_tree()
        self.assertGreater(collapse.rect.h, height)
        self.assertEqual(collapse.container.rect.top, collapse.toggle.rect.bottom)
        collapse.state.value = False
        self.root.update_tree()
        self.assertEqual(collapse.rect.h, height)

    def test_controls_tolerate_zero_allocation(self):
        widgets = [bf.gui.Slider("Volume"), bf.gui.Toggle("Enabled"),
                   bf.gui.Selector("Mode", ["a", "b"]), bf.gui.TextInput("Hello"),
                   bf.gui.Image().from_surface(pygame.Surface((20, 20)))]
        for widget in widgets:
            with self.subTest(widget=type(widget).__name__):
                widget.measure((0, 0))
                widget.arrange((0, 0))
                widget.paint_tree()
                self.assertEqual(widget.rect.size, (0, 0))

    def test_measure_then_arrange_order(self):
        calls = []

        class Probe(bf.gui.Widget):
            def __init__(self, name):
                super().__init__()
                self.name = name

            def measure(self, size):
                calls.append(("measure", self.name))
                return super().measure(size)

            def arrange(self, rect):
                calls.append(("arrange", self.name))
                super().arrange(rect)

        parent, child = Probe("parent"), Probe("child")
        parent.add(child)
        self.update(parent)
        self.assertEqual(calls, [("measure", "parent"), ("measure", "child"),
                                 ("arrange", "parent"), ("arrange", "child")])

    def test_arrangement_cannot_resize_its_allocation(self):
        class Resizer(bf.gui.Widget):
            def arrange_override(self):
                self.set_size((999, 999))

        widget = Resizer()
        widget.measure((50, 50))
        widget.arrange((20, 30))
        self.assertEqual(widget.rect.size, (20, 30))

    def test_partial_size_change_keeps_original_request(self):
        widget = self.box(200, 40).set_autoresize(False)
        widget.measure((50, 50))
        widget.arrange((50, 40))
        widget.set_size((None, 20))
        self.assertEqual(widget.measure((400, 400)), (200, 20))


if __name__ == "__main__":
    unittest.main()

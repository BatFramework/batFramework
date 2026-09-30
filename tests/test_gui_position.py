"""Position policies use final parent bounds and preserve assigned sizes."""
import os
from pathlib import Path
import sys
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame
import batFramework as bf


class PositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((800, 600))
        bf.FontManager().init_font(None)

    def parent_and_child(self, *constraints):
        parent = bf.gui.Shape((200, 120)).set_position(40, 60)
        parent.set_padding((10, 5, 30, 15)).set_relief(10)
        child = bf.gui.Shape((20, 10)).add_constraints(*constraints)
        parent.add(child)
        return parent, child

    def test_every_anchor_is_pure_and_uses_content_bounds(self):
        proposed = pygame.FRect(3, 7, 20, 10)
        outer = pygame.FRect(40, 60, 200, 120)
        inner = pygame.FRect(50, 65, 160, 90)
        originals = [r.copy() for r in (proposed, outer, inner)]
        for name in ("AnchorTop", "AnchorBottom", "AnchorLeft", "AnchorRight",
                     "AnchorTopLeft", "AnchorTopRight", "AnchorBottomLeft",
                     "AnchorBottomRight", "Center", "CenterX", "CenterY"):
            with self.subTest(anchor=name):
                anchor = getattr(bf.gui, name)()
                result = anchor.constrain_position(proposed, outer, inner)
                self.assertEqual(getattr(result, anchor.edge), getattr(inner, anchor.edge))
                self.assertEqual(result.size, proposed.size)
                self.assertEqual([proposed, outer, inner], originals)
                self.assertIsNot(result, proposed)

    def test_margins_are_pure_for_every_unit(self):
        proposed = pygame.FRect(3, 7, 20, 10)
        outer = pygame.FRect(40, 60, 200, 120)
        inner = pygame.FRect(50, 65, 160, 90)
        originals = [r.copy() for r in (proposed, outer, inner)]
        for unit, expected in ((bf.unit.PIXELS, (55, 72)),
                               (bf.unit.PERCENTAGE, (58, 71.3)),
                               (bf.unit.PERCENTAGE_RECT, (50, 68.4))):
            with self.subTest(unit=unit):
                left, top = (5, 7) if unit == bf.unit.PIXELS else (.05, .07)
                result = bf.gui.Margin(left=left, top=top, unit=unit).constrain_position(proposed, outer, inner)
                self.assertAlmostEqual(result.x, expected[0], places=4)
                self.assertAlmostEqual(result.y, expected[1], places=4)
                self.assertEqual(result.size, proposed.size)
                self.assertEqual([proposed, outer, inner], originals)

    def test_measure_never_invokes_position_hooks(self):
        class PositionProbe(bf.gui.Constraint):
            def __init__(self):
                super().__init__()
                self.affects_position = True

            def constrain_position(self, *args):
                raise AssertionError("Positioning during measurement")

        parent, child = self.parent_and_child(PositionProbe())
        before = child.rect.copy()
        parent.measure((800, 600))
        self.assertEqual(child.rect, before)

    def test_arrange_uses_new_allocation(self):
        parent, child = self.parent_and_child(bf.gui.AnchorBottomRight(), bf.gui.MarginRight(7))
        child.arrange((0, 0, 50, 25))
        self.assertEqual(child.rect, pygame.FRect(153, 130, 50, 25))

    def test_position_committed_once_after_all_policies(self):
        class Probe(bf.gui.Shape):
            def set_position(self, x=None, y=None):
                self.positions.append((x, y))
                return super().set_position(x, y)

        parent = bf.gui.Shape((200, 120))
        child = Probe((20, 10))
        child.positions = []
        child.add_constraints(bf.gui.Center(), bf.gui.MarginLeft(5), bf.gui.MarginTop(7))
        parent.add(child)
        child.arrange((20, 10))
        self.assertEqual(child.positions, [(5, 7)])

    def test_priorities_and_insertion_order(self):
        parent, child = self.parent_and_child(bf.gui.AnchorRight().set_priority(5), bf.gui.MarginLeft(7))
        child.arrange((20, 10))
        self.assertEqual(child.rect.right, parent.get_inner_rect().right)
        child.constraints[1].set_priority(5)
        child.arrange((20, 10))
        self.assertEqual(child.rect.left, parent.get_inner_rect().left + 7)

    def test_opposing_margins_do_not_stretch(self):
        parent, child = self.parent_and_child(bf.gui.Margin(1, 2, 3, 4))
        child.arrange((20, 10))
        inner = parent.get_inner_rect()
        self.assertEqual(child.rect.size, (20, 10))
        self.assertEqual(child.rect.bottomright, (inner.right - 3, inner.bottom - 4))
        self.assertEqual(child.constrain_position(child.rect), child.rect)

    def test_unset_edges_and_negative_margins(self):
        parent, child = self.parent_and_child(bf.gui.MarginLeft(-5))
        child.arrange((20, 30, 20, 10))
        self.assertEqual(child.rect.topleft, (parent.get_inner_rect().left - 5, 30))

    def test_parent_resize_and_repeated_arrangement(self):
        parent, child = self.parent_and_child(bf.gui.PercentageMarginRight(.1), bf.gui.PercentageMarginBottom(.2))
        for size in ((200, 120), (400, 300), (150, 100)):
            parent.set_size(size)
            for _ in range(3):
                child.arrange((20, 10))
                inner = parent.get_inner_rect()
                self.assertAlmostEqual(child.rect.right, inner.right - inner.w * .1, places=4)
                self.assertAlmostEqual(child.rect.bottom, inner.bottom - inner.h * .2, places=4)

    def test_descendants_arrange_at_final_parent_position(self):
        outer = bf.gui.Shape((400, 300))
        panel = bf.gui.Container(bf.gui.Column(), bf.gui.Shape((30, 15))).set_padding(4)
        panel.add_constraints(bf.gui.AnchorBottomRight(), bf.gui.MarginRight(10))
        outer.add(panel)
        outer.measure((400, 300))
        outer.arrange((400, 300))
        self.assertEqual(panel.rect.bottomright, (390, 300))
        self.assertEqual(panel.children[0].rect.topleft, panel.get_inner_rect().topleft)

    def test_custom_position_hook_and_invalid_size_change(self):
        class CustomPosition(bf.gui.Constraint):
            def __init__(self):
                super().__init__()
                self.affects_position = True

            def constrain_position(self, proposed, outer, inner):
                result = proposed.copy()
                result.midleft = inner.midleft
                return result

        parent, child = self.parent_and_child(CustomPosition())
        before = child.rect.copy()
        proposed = pygame.FRect(0, 0, 50, 25)
        result = child.constrain_position(proposed)
        self.assertEqual(child.rect, before)
        self.assertEqual(result.midleft, parent.get_inner_rect().midleft)
        child.constraints[0].constrain_position = lambda proposed, outer, inner: proposed.inflate(1, 1)
        with self.assertRaisesRegex(ValueError, "preserve the assigned size"):
            child.arrange(proposed)
        self.assertEqual(child.rect, before)


if __name__ == "__main__":
    unittest.main()

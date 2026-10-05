"""Safe placement of floating rectangles without changing caller geometry."""
import os
from pathlib import Path
import sys
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame
from batFramework.gui import fit_rect, inset_rect


class GeometryTests(unittest.TestCase):
    def test_preserves_preferred_position_size_and_inputs(self):
        rect = pygame.FRect(1, 2, 30.5, 20.5)
        bounds = pygame.FRect(100, 200, 100, 100)
        before = rect.copy(), bounds.copy()
        placed = fit_rect(rect, bounds, (110.25, 220.75), margin=4)
        self.assertEqual(placed, pygame.FRect(110.25, 220.75, 30.5, 20.5))
        self.assertEqual((rect, bounds), before)

    def test_clamps_each_edge_with_margin(self):
        rect = pygame.Rect(0, 0, 30, 20)
        bounds = pygame.Rect(100, 200, 100, 100)
        for preferred, expected in (
            ((0, 0), (104, 204)),
            ((300, 400), (166, 276)),
            ((120, 400), (120, 276)),
            ((300, 220), (166, 220)),
        ):
            with self.subTest(preferred=preferred):
                placed = fit_rect(rect, bounds, preferred, margin=4)
                self.assertEqual(placed.topleft, expected)
                self.assertEqual(placed.size, rect.size)

    def test_oversized_dimensions_shrink_independently(self):
        bounds = pygame.FRect(100, 200, 100, 100)
        for size, expected in (
            ((200, 20), (92, 20)),
            ((30, 200), (30, 92)),
            ((200, 200), (92, 92)),
        ):
            with self.subTest(size=size):
                placed = fit_rect(pygame.FRect(0, 0, *size), bounds, (110, 210), 4)
                self.assertEqual(placed.size, expected)
                self.assertTrue(inset_rect(bounds, 4).contains(placed))

    def test_tiny_bounds_and_excessive_margins_collapse_at_center(self):
        for size in ((2, 2), (0, 0), (10, 20)):
            with self.subTest(size=size):
                bounds = pygame.FRect(100, 200, *size)
                placed = fit_rect(pygame.FRect(0, 0, 30, 20), bounds, (0, 0), 100)
                self.assertEqual(placed.size, (0, 0))
                self.assertEqual(placed.topleft, bounds.center)

    def test_negative_margin_does_not_expand_bounds(self):
        bounds = pygame.FRect(100, 200, 100, 100)
        self.assertEqual(inset_rect(bounds, -10), bounds)
        placed = fit_rect(pygame.FRect(0, 0, 30, 20), bounds, (0, 0), -10)
        self.assertEqual(placed.topleft, bounds.topleft)


if __name__ == "__main__":
    unittest.main()

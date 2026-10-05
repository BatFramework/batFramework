"""Shared geometry for floating GUI elements, in GUI world coordinates."""

import pygame


def inset_rect(rect: pygame.Rect | pygame.FRect, margin: float = 0) -> pygame.FRect:
    """Return safe bounds, capping a nonnegative margin at half each dimension."""
    bounds = pygame.FRect(rect)
    margin = max(0, margin)
    mx = min(margin, bounds.width / 2)
    my = min(margin, bounds.height / 2)
    return pygame.FRect(bounds.x + mx, bounds.y + my,
                        max(0, bounds.width - 2 * mx),
                        max(0, bounds.height - 2 * my))


def fit_rect(
    rect: pygame.Rect | pygame.FRect,
    bounds: pygame.Rect | pygame.FRect,
    preferred_topleft: tuple[float, float],
    margin: float = 0,
) -> pygame.FRect:
    """Place a copy as close as possible to the preferred top-left inside bounds.

    The safety margin is applied on all sides. Preserve size when it fits;
    otherwise shrink only the oversized dimensions to the available space.
    Negative margins act as zero; excessive margins leave zero space on the
    affected axes. Neither input rectangle is modified.
    """
    safe_bounds = inset_rect(bounds, margin)
    placed = pygame.FRect(rect)
    placed.size = (min(max(0, placed.width), safe_bounds.width),
                   min(max(0, placed.height), safe_bounds.height))
    placed.topleft = preferred_topleft
    placed.clamp_ip(safe_bounds)
    return placed

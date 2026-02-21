from __future__ import annotations
import pygame
import batFramework as bf
from typing import NamedTuple, Sequence


class LayoutSlot(NamedTuple):
    size: tuple[float, float]  # (w, h) of this item
    weight: float = 0  # >0 means it stretches to fill remaining space


def distribute_horizontal(
    slots: Sequence[LayoutSlot],
    rect: pygame.FRect,
    gap: float = 0,
    alignment: bf.alignment = bf.alignment.LEFT,
) -> list[pygame.FRect]:
    """
    Given a list of slots and a bounding rect, returns positioned FRects.
    Slots with weight > 0 share the leftover space proportionally.
    """
    fixed_w = sum(s.size[0] for s in slots if s.weight == 0)
    total_gap = gap * (len(slots) - 1)
    leftover = max(0.0, rect.width - fixed_w - total_gap)
    total_weight = sum(s.weight for s in slots if s.weight > 0)

    widths: list[float] = []
    for slot in slots:
        if slot.weight > 0 and total_weight > 0:
            widths.append(leftover * slot.weight / total_weight)
        else:
            widths.append(slot.size[0])

    total_w = sum(widths) + total_gap
    start_x = {
        bf.alignment.LEFT: rect.left,
        bf.alignment.MIDLEFT: rect.left,
        bf.alignment.CENTER: rect.centerx - total_w / 2,
        bf.alignment.RIGHT: rect.right - total_w,
        bf.alignment.MIDRIGHT: rect.right - total_w,
    }.get(alignment, rect.left)

    result: list[pygame.FRect] = []
    x = start_x
    for slot, w in zip(slots, widths):
        h = slot.size[1]
        r = pygame.FRect(x, rect.centery - h / 2, w, h)
        result.append(r)
        x += w + gap

    return result


def distribute_vertical(
    slots: Sequence[LayoutSlot],
    rect: pygame.FRect,
    gap: float = 0,
    alignment: bf.alignment = bf.alignment.CENTER,
) -> list[pygame.FRect]:
    fixed_h = sum(s.size[1] for s in slots if s.weight == 0)
    total_gap = gap * (len(slots) - 1)
    leftover = max(0.0, rect.height - fixed_h - total_gap)
    total_weight = sum(s.weight for s in slots if s.weight > 0)

    heights: list[float] = []
    for slot in slots:
        if slot.weight > 0 and total_weight > 0:
            heights.append(leftover * slot.weight / total_weight)
        else:
            heights.append(slot.size[1])

    total_h = sum(heights) + total_gap
    start_y = {
        bf.alignment.TOP: rect.top,
        bf.alignment.CENTER: rect.centery - total_h / 2,
        bf.alignment.BOTTOM: rect.bottom - total_h,
    }.get(alignment, rect.top)

    result: list[pygame.FRect] = []
    y = start_y
    for slot, h in zip(slots, heights):
        w = slot.size[0]
        r = pygame.FRect(rect.centerx - w / 2, y, w, h)
        result.append(r)
        y += h + gap

    return result

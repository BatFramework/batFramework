import pygame
import batFramework as bf
from .container import Container
from .shape import Shape
from .widget import Widget
from .layout import Layout
from .interactiveWidget import InteractiveWidget
from .draggableWidget import DraggableWidget
from typing import Self

# ── ScrollingContainer ────────────────────────────────────────────────────────

class ScrollingContainer(Container):


    # ── Scrollbar track ───────────────────────────────────────────────────────────

    class _ScrollTrack(Shape, InteractiveWidget):
        """
        The background rail of a scrollbar.
        Clicking it jumps the scroll so the handle centers on the click point.
        Style it freely via the Shape API (set_color, set_texture, etc.).
        """

        def __init__(self, vertical: bool) -> None:
            self._vertical = vertical
            super().__init__()
            self.set_autoresize(False)
            self.set_color((0, 0, 0, 40))

        def do_on_click_down(self, button: int, event=None) -> None:
            if button != 1:
                return
            sc: "ScrollingContainer" = self.parent
            if sc is None or not sc.parent_layer:
                return

            handle = sc.v_handle if self._vertical else sc.h_handle
            mouse  = sc.parent_layer.camera.get_mouse_pos()

            if self._vertical:
                content    = sc.layout.children_rect.height
                viewport   = sc.get_inner_rect().height
                handle_len = handle.rect.height
                track_len  = self.rect.height
                local      = mouse[1] - self.rect.top
            else:
                content    = sc.layout.children_rect.width
                viewport   = sc.get_inner_rect().width
                handle_len = handle.rect.width
                track_len  = self.rect.width
                local      = mouse[0] - self.rect.left

            usable     = track_len - handle_len
            max_scroll = max(0, content - viewport)
            if usable <= 0 or max_scroll <= 0:
                return

            ratio = max(0.0, min(1.0, (local - handle_len * 0.5) / usable))
            if self._vertical:
                sc.set_scroll((sc.scroll.x, ratio * max_scroll))
            else:
                sc.set_scroll((ratio * max_scroll, sc.scroll.y))

            #handle.is_dragged = True


    # ── Scrollbar handle ──────────────────────────────────────────────────────────

    class _ScrollHandle(Shape, DraggableWidget):
        """
        The draggable thumb of a scrollbar.
        Dragging it updates the parent ScrollingContainer's scroll position.
        Hover and drag states are reflected visually; override paint() for custom looks.
        Style it freely via the Shape API (set_color, set_texture, etc.).
        """

        def __init__(self, vertical: bool) -> None:
            self._vertical      = vertical
            self._prev_dragging = False
            super().__init__()
            self.set_autoresize(False)
            


        # on_enter / on_exit already set dirty_surface via InteractiveWidget — no override needed.

        def update(self, dt: float) -> None:
            super().update(dt)
            # Repaint when drag state transitions so the color updates immediately.
            dragging = self.is_dragged or self.is_dragged_outside
            if dragging != self._prev_dragging:
                self._prev_dragging = dragging
                self.dirty_surface  = True

        def paint(self) -> None:
            super().paint()

        def do_on_drag(self, drag_start, drag_end) -> None:
            """Translate mouse position into a scroll ratio and push it to the parent."""
            sc: "ScrollingContainer" = self.parent
            if sc is None or not sc.layout or not sc.parent_layer:
                return

            track = sc.v_track if self._vertical else sc.h_track
            mouse = sc.parent_layer.camera.get_mouse_pos()

            if self._vertical:
                content    = sc.layout.children_rect.height
                viewport   = sc.get_inner_rect().height
                handle_len = self.rect.height
                track_len  = track.rect.height
                pos        = mouse[1] - self.offset[1] - track.rect.top
            else:
                content    = sc.layout.children_rect.width
                viewport   = sc.get_inner_rect().width
                handle_len = self.rect.width
                track_len  = track.rect.width
                pos        = mouse[0] - self.offset[0] - track.rect.left

            usable     = track_len - handle_len
            max_scroll = max(0, content - viewport)
            if usable <= 0 or max_scroll <= 0:
                return

            ratio = max(0.0, min(1.0, pos / usable))
            if self._vertical:
                sc.set_scroll((sc.scroll.x, ratio * max_scroll))
            else:
                sc.set_scroll((ratio * max_scroll, sc.scroll.y))


    def __init__(self, layout: Layout = None, *children: Widget) -> None:
        self._scrollbar_thickness: float = 8
        self._scroll_speed: float        = 20.0

        # Public shape handles — style these directly.
        self.v_track  = ScrollingContainer._ScrollTrack(vertical=True)
        self.v_handle = ScrollingContainer._ScrollHandle(vertical=True)
        self.h_track  = ScrollingContainer._ScrollTrack(vertical=False)
        self.h_handle = ScrollingContainer._ScrollHandle(vertical=False)
        self._scrollbar_widgets = (self.v_track, self.v_handle, self.h_track, self.h_handle)

        super().__init__(layout, *children)

        for sb in self._scrollbar_widgets:
            sb.set_visible(False)
            self.add(sb)
            sb.set_render_order(999)   # always on top of content

        self.set_clip_children(True)
        self.set_debug_color("teal")

    def __str__(self) -> str:
        return f"ScrollingContainer({self.uid},{len(self.children)})"

    # ── Configuration ─────────────────────────────────────────────────────────

    def set_scrollbar_thickness(self, thickness: float) -> Self:
        thickness = max(2, thickness)
        if self._scrollbar_thickness != thickness:
            self._scrollbar_thickness = thickness
            self.dirty_layout = True
        return self

    def set_scroll_speed(self, speed: float) -> Self:
        self._scroll_speed = max(1.0, speed)
        return self

    # ── Exclude scrollbar widgets from the layout ─────────────────────────────

    def get_layout_children(self):
        return [c for c in super().get_layout_children() if c not in self._scrollbar_widgets]

    # ── Inner rect (shrinks to make room for visible scrollbars) ──────────────

    def _base_inner_rect(self) -> pygame.FRect:
        return super().get_inner_rect()

    def get_inner_rect(self) -> pygame.FRect:
        r = super().get_inner_rect()
        if self.v_track.visible:
            r.width  = max(0, r.width  - self._scrollbar_thickness)
        if self.h_track.visible:
            r.height = max(0, r.height - self._scrollbar_thickness)
        return r

    def get_local_inner_rect(self) -> pygame.FRect:
        r = super().get_local_inner_rect()
        if self.v_track.visible:
            r.width  = max(0, r.width  - self._scrollbar_thickness)
        if self.h_track.visible:
            r.height = max(0, r.height - self._scrollbar_thickness)
        return r


    def top_at(self, x: float | int, y: float | int) -> "None|Widget":
        # first check if the point is inside the scrollbar handles and then tracks
        r = self.v_handle.top_at(x, y)
        if r is not None:
            return r
        r = self.v_track.top_at(x, y)
        if r is not None:
            return r
        r = self.h_handle.top_at(x, y)
        if r is not None:
            return r
        r = self.h_track.top_at(x, y)
        if r is not None:
            return r
        return super().top_at(x, y)

    # ── Scrollbar visibility ──────────────────────────────────────────────────

    def _update_scrollbar_visibility(self) -> bool:
        """Show/hide track+handle pairs. Returns True if anything changed."""
        old_v = self.v_track.visible
        old_h = self.h_track.visible

        if not self.get_layout_children():
            need_v = need_h = False
        else:
            base   = self._base_inner_rect()
            cw, ch = self.layout.children_rect.width, self.layout.children_rect.height
            t      = self._scrollbar_thickness

            need_h = cw > base.width
            need_v = ch > base.height
            # one scrollbar may push the other axis over the threshold
            if need_v and not need_h: need_h = cw > base.width  - t
            if need_h and not need_v: need_v = ch > base.height - t

        for w in (self.v_track, self.v_handle): w.set_visible(need_v)
        for w in (self.h_track, self.h_handle): w.set_visible(need_h)

        return old_v != need_v or old_h != need_h

    # ── Scrollbar geometry ────────────────────────────────────────────────────

    def _update_scrollbar_rects(self) -> None:
        """Position and size track+handle widgets to match current scroll state."""
        base  = self._base_inner_rect()
        inner = self.get_inner_rect()
        t     = self._scrollbar_thickness

        if self.v_track.visible:
            track_rect = pygame.FRect(base.right - t, base.top, t, inner.height)
            self.v_track.set_position(*track_rect.topleft)
            self.v_track.set_size(track_rect.size)

            ch       = self.layout.children_rect.height
            vh       = inner.height
            handle_h = max(t, self.v_track.get_inner_height() * min(1.0, vh / ch) if ch > 0 else t)
            sr       = self.scroll.y / max(1, ch - vh)
            self.v_handle.set_size((self.v_track.get_inner_width(), handle_h))
            self.v_handle.set_position(
                self.v_track.get_inner_left(),
                self.v_track.get_inner_top() + sr * (self.v_track.get_inner_height() - handle_h)
            )

        if self.h_track.visible:
            track_rect = pygame.FRect(base.left, base.bottom - t, inner.width, t)
            self.h_track.set_position(*track_rect.topleft)
            self.h_track.set_size(track_rect.size)

            cw       = self.layout.children_rect.width
            vw       = inner.width
            handle_w = max(t, self.h_track.get_inner_width() * min(1.0, vw / cw) if cw > 0 else t)
            sr       = self.scroll.x / max(1, cw - vw)
            self.h_handle.set_size((handle_w, self.h_track.get_inner_height()))
            self.h_handle.set_position(
                self.h_track.get_inner_left() + sr * (self.h_track.get_inner_width() - handle_w),
                self.h_track.get_inner_top()
            )

    # ── Events ────────────────────────────────────────────────────────────────

    def handle_event(self, event) -> None:
        # Old-style pygame scroll buttons — swallow so they don't trigger clicks.
        if (
            event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP)
            and event.button in (4, 5)
            and (self.v_track.visible or self.h_track.visible)
            and self.parent_layer
            and self.rect.collidepoint(*self.parent_layer.camera.get_mouse_pos())
        ):
            event.consumed = True
            return

        self._handle_mouse_wheel(event)
        super().handle_event(event)

    def _handle_mouse_wheel(self, event) -> None:
        if event.type != pygame.MOUSEWHEEL or not self.parent_layer:
            return
        # Use rect collision instead of is_hovered so scrolling works even
        # when the mouse is hovering a child scrollbar widget.
        if not self.rect.collidepoint(*self.parent_layer.camera.get_mouse_pos()):
            return
        if not self.v_track.visible and not self.h_track.visible:
            return

        keys  = pygame.key.get_pressed()
        shift = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        delta = event.y or event.x
        if not delta:
            return

        amount = self._scroll_speed * (1 if delta < 0 else -1)

        if   shift             and self.h_track.visible: self.scrollX_by(amount)
        elif not shift         and self.v_track.visible: self.scrollY_by(amount)
        elif self.h_track.visible:                       self.scrollX_by(amount)
        elif self.v_track.visible:                       self.scrollY_by(amount)
        else: return

        event.consumed = True

    # ── Update pipeline ───────────────────────────────────────────────────────

    def apply_post_updates(self, skip_draw: bool = False) -> None:
        # ── 1. Resolve own size ───────────────────────────────────────────────
        if self.dirty_shape:
            if self.build():
                # Our rect changed — layout must re-run to reflow children.
                self.dirty_layout               = True
                self.dirty_size_constraints     = True
                self.dirty_position_constraints = True
            self.dirty_shape   = False
            self.dirty_surface = True

        # ── 2. Position constraints (after size is stable) ────────────────────
        if self.dirty_position_constraints:
            self.resolve_constraints(position_only=True)
            self.dirty_position_constraints = False

        # ── 3. Layout (after our rect is stable) ──────────────────────────────
        if self.dirty_layout:
            self.layout.update_child_constraints()
            self.layout.arrange()
            self.dirty_layout  = False
            self.dirty_surface = True

        # ── 4. Scrollbar visibility (may shrink inner rect → re-arrange) ──────
        if self._update_scrollbar_visibility():
            self.layout.arrange()
            self.dirty_surface = True

        # ── 5. Clamp + sync children (once, covers layout shifts and dirty_scroll)
        old_scroll = self.scroll.xy
        self.clamp_scroll()

        if self.scroll.xy != old_scroll or self.dirty_scroll:
            self.layout.scroll_children()
            self.dirty_scroll  = False
            self.dirty_surface = True

        # ── 6. Position scrollbar widgets to match current scroll state ───────
        self._update_scrollbar_rects()

        # ── 7. Paint ──────────────────────────────────────────────────────────
        if self.dirty_surface and not skip_draw:
            self.paint()
            self.dirty_surface = False

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, camera: bf.Camera) -> None:
        # 1. Draw our own surface.
        bf.Drawable.draw(self, camera)

        # 2. Draw content children inside the clipped viewport.
        old_clip     = camera.surface.get_clip()
        content_clip = camera.world_to_screen(self.get_inner_rect()).clip(old_clip)
        camera.surface.set_clip(content_clip)

        for child in self.children:
            if child in self._scrollbar_widgets:
                continue
            if child.rect.colliderect(self.rect) or not child.rect:
                child.draw(camera)

        camera.surface.set_clip(old_clip)

        # 3. Draw track and handle on top, unclipped.
        for sb in self._scrollbar_widgets:
            if sb.visible:
                sb.draw(camera)
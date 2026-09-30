"""An asset-free GUI playground and repeatable layout stress test.

Run from a checkout (imports this checkout's src, not an installed wheel):
    python examples/gui_stress_demo.py
    python examples/gui_stress_demo.py --cards 150 --depth 12
    python examples/gui_stress_demo.py --headless --frames 180 --exercise
    python examples/gui_stress_demo.py --headless --frames 1 --screenshot preview.png
    python examples/gui_stress_demo.py --headless --frames 180 --exercise --profile gui-stress.prof


Resize the window, drag the sliders and scrollbars, open dropdowns, type into
the inputs, and expand nested panels. Wheel at a nested viewport's boundary
should bubble to its parent. Shift+wheel scrolls horizontally. F1 toggles debug
outlines; Escape exits. --exercise drives controls and resizes automatically.
"""
from __future__ import annotations

import argparse
import cProfile
from collections import deque
from contextlib import nullcontext
import io
import logging
import math
import os
import pstats
from pathlib import Path
import sys
from time import perf_counter

if "--headless" in sys.argv:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pygame
import batFramework as bf
from batFramework.gui.slider import SliderHandle

BG = "#101723"
PANEL = "#1b2738"
FIELD = "#26364d"
TEXT = "#e7eef9"
MUTED = "#a1b4cc"
ACCENT = "#67dbc1"
BLUE = "#82b7ff"


class StressStyle(bf.gui.Style):
    """Shared widget appearance, applied automatically by StyleManager."""

    def apply(self, w):
        if isinstance(w, bf.gui.Shape):
            w.set_color(PANEL).set_outline_width(0).set_border_radius(4)
        if isinstance(w, bf.gui.Label):
            w.set_text_color(TEXT).set_text_bg_color(None).set_font_size(18)
        if isinstance(w, bf.gui.Button):
            w.set_color(FIELD).set_padding((8, 5))
            if isinstance(w, (bf.gui.Slider, bf.gui.Toggle, bf.gui.Selector)):
                w.set_gap(8)
        if isinstance(w, bf.gui.TextInput):
            w.set_color(BG).set_padding(8).set_outline_width(1).set_outline_color(BLUE)
        if isinstance(w, bf.gui.ArrowIndicator):
            w.set_arrow_color(TEXT)
        if isinstance(w, SliderHandle):
            w.set_color(ACCENT).set_outline_width(0)
        if isinstance(w, bf.gui.ToggleIndicator):
            w.set_on_color(ACCENT)
            w.set_off_color(MUTED)
            w.set_value(w.get_value())


class StressCompositeStyle(bf.gui.Style):
    """Apply after basic rules so child visuals retain their specific roles."""

    def apply(self, w):
        if isinstance(w, bf.gui.Dropdown):
            w.panel.set_color(BG).set_outline_width(1).set_outline_color(BLUE)
        if isinstance(w, bf.gui.BarMeter):
            w.set_color(BG)
            w.content.set_color(BLUE)
        if isinstance(w, bf.gui.ScrollingContainer):
            w.set_scrollbar_thickness(12).set_scroll_speed(32)
            for track in (w.h_track, w.v_track):
                track.set_padding(0).set_relief(0).set_color(BG)
                track.handle.set_color(ACCENT)


def label(text, size=18):
    return (bf.gui.Label(text).set_font_size(size)
            .set_alignment(bf.alignment.LEFT).set_padding(0))


def column(*children, gap=8):
    return bf.gui.Container(bf.gui.Column(gap).set_child_constraints(bf.gui.FillX()), *children)


def row(*children, gap=8):
    return bf.gui.Container(bf.gui.Row(gap), *children).set_padding(0)


def section(title, *children):
    return column(label(title).set_bold(True), *children).set_padding(12)


def fixed(widget, width=None, height=None):
    if width is not None:
        widget.add_constraints(bf.gui.Width(width))
    if height is not None:
        widget.add_constraints(bf.gui.Height(height))
    return widget


class GuiStressDemo(bf.Scene):
    def __init__(self, cards=48, depth=6):
        super().__init__("gui-stress")
        self.set_clear_color(BG)
        self.level = bf.gui.SyncedVar(0.4)
        self.animate = bf.gui.SyncedVar(True)
        self.choice = bf.gui.SyncedVar("Balanced")
        self.message = bf.gui.SyncedVar("Edit either input; both share the same text.")
        self.collapses = []
        self.inputs = []
        self.elapsed = 0.0
        self.frames = 0
        self.last_report = 0.0
        self.last_update_ms = 0.0
        self.last_draw_ms = 0.0
        self.frame_samples = deque(maxlen=600)
        self.root.add(bf.gui.BasicDebugger().add_constraints(bf.gui.AnchorTopRight()))

        self.status = label("Starting GUI...").add_constraints(bf.gui.Height(24))
        self.value_label = label("Shared value: 40%")
        self.level.bind(self.value_label, lambda v: self.value_label.set_text(f"Shared value: {v:.0%}"))
        self.pulse = bf.PropertyEaser(duration=2.0, easing=bf.easing.EASE_IN_OUT, register=self.name)
        # Sliders can return integer endpoints; PropertyEaser expects matching
        # start/end types, so normalize the animation's starting value.
        self.pulse.add_custom(lambda: float(self.level.value), self.level.set_value, 0.9)
        self.animate.bind(self, lambda enabled: None if enabled else self.pulse.stop())

        self.load_grid = bf.gui.Container(bf.gui.Grid(1, 3, 8)).set_padding(0)
        self.load_count = label("")
        self.add_cards(cards)
        self.gallery = bf.gui.ScrollingContainer(bf.gui.Column(12).set_child_constraints(bf.gui.FillX()))
        self.gallery.set_scroll_x_enabled(False).set_padding(8)
        self.gallery.add_constraints(bf.gui.GrowH(), bf.gui.FillY())
        self.gallery.add(self.make_values(), self.make_text(), self.make_nested(depth),
                         self.make_layouts(), self.make_load())

        self.sidebar = bf.gui.ScrollingContainer(bf.gui.Column(12).set_child_constraints(bf.gui.FillX()))
        self.sidebar.set_scroll_x_enabled(False).set_padding(8)
        self.sidebar.add_constraints(bf.gui.Width(285), bf.gui.FillY())
        self.sidebar.add(self.make_controls(), self.make_help())
        body = row(self.sidebar, self.gallery, gap=12).add_constraints(bf.gui.GrowV(), bf.gui.FillX())
        heading = column(label("GUI / Stress laboratory", 28).set_bold(True),
                         label("Nested layouts, live bindings, animated values and deliberate overflow."), gap=4)
        self.shell = column(heading, body, self.status, gap=12).set_padding(16)
        self.shell.add_constraints(bf.gui.Fill())
        self.root.add(self.shell)
        self.root.set_show_tooltip(True)

    def make_controls(self):
        self.dropdown = bf.gui.Dropdown(["Balanced", "Fast", "Precise"], synced_var=self.choice)
        self.selector = bf.gui.Selector("Mode", ["Balanced", "Fast", "Precise"], synced_var=self.choice)
        self.selector.set_allow_cycle(True)
        radios = column(*(bf.gui.RadioButton(name, self.choice) for name in ("Balanced", "Fast", "Precise")))
        self.mode_label = label("Mode: Balanced")
        self.choice.bind(self.mode_label, lambda value: self.mode_label.set_text(f"Mode: {value}"))
        return section("Control desk",
                       bf.gui.Toggle("Animate shared value", synced_var=self.animate),
                       bf.gui.Button("Animate to a new value", self.retarget),
                       self.mode_label, self.dropdown, self.selector, radios,
                       bf.gui.Button("Toggle debug outlines [F1]", self.toggle_debug),
                       bf.gui.Button("Reset all scroll positions", self.reset_scroll),
                       bf.gui.Button("Expand / collapse all", self.toggle_collapses))

    def make_help(self):
        text = label("Try the wheel inside nested panels. At either end, it passes to the outer panel. "
                     "Use Shift+wheel for horizontal scrolling. Drag the mint handles. "
                     "Resize the window to exercise wrapping and viewport negotiation.").set_auto_wraplength(True)
        hover = bf.gui.Button("Hover for a tooltip", lambda: self.message.set_value("Tooltip button clicked."))
        hover.set_tooltip_text("ToolTip: follows the pointer and stays within the window.")
        disabled = bf.gui.Button("Disabled button").disable()
        return section("Things to try", text, hover, disabled)

    def make_values(self):
        a = bf.gui.Slider("Source", synced_var=self.level).set_range(0.0, 1.0).set_step(.01)
        b = bf.gui.Slider("Mirror", synced_var=self.level).set_range(0.0, 1.0).set_step(.01)
        meter = fixed(bf.gui.BarMeter(0.0, 1.0, synced_var=self.level), height=18)
        vertical = fixed(bf.gui.Slider("", synced_var=self.level).set_direction(bf.direction.DOWN), 36, 100)
        description = column(self.value_label, a, b, meter).set_padding(0).add_constraints(bf.gui.GrowH())
        return section("01 / One value, four views", row(description, vertical, gap=18),
                       label("Pause animation in the control desk to drag either slider.").set_auto_wraplength(True))

    def make_text(self):
        for _ in range(2):
            entry = fixed(bf.gui.TextInput(self.message.value, placeholder_text="Type here..."), height=42)
            entry.set_modify_callback(self.message.set_value)
            self.message.bind(entry, lambda text, entry=entry: entry.set_text(text))
            self.inputs.append(entry)
        self.typewriter = bf.gui.AnimatedLabel("AnimatedLabel reveals this sentence one character at a time.")
        self.typewriter.set_text_speed(.035).set_auto_wraplength(True)
        rich = bf.gui.Label("**Rich text** with *italics*, __underlining__, and [color=#67dbc1]color[/color].",
                            renderer=bf.gui.RichTextRenderer()).set_auto_wraplength(True)
        tile = pygame.Surface((72, 72), pygame.SRCALPHA)
        pygame.draw.circle(tile, ACCENT, (36, 36), 31)
        pygame.draw.polygon(tile, BG, ((27, 18), (53, 36), (27, 54)))
        image = fixed(bf.gui.Image().from_surface(tile), 72, 72)
        preview = row(image, column(rich, fixed(self.typewriter, height=65)).add_constraints(bf.gui.GrowH()))
        return section("02 / Text, image and keyboard input", *self.inputs, preview,
                       bf.gui.Button("Replay typewriter", lambda: self.typewriter.set_text(self.typewriter.original_text)))

    def make_nested(self, depth):
        chips = [fixed(bf.gui.Button(f"Chip {i + 1}", lambda i=i: self.message.set_value(f"Selected chip {i + 1}")),
                       115, 38) for i in range(12)]
        horizontal = bf.gui.ScrollingContainer(bf.gui.Row(8), *chips).set_scroll_y_enabled(False)
        horizontal.set_padding(8).add_constraints(bf.gui.Height(80))
        nested = section("Deepest leaf", label("This input sits at the bottom of the nesting tree."),
                         fixed(bf.gui.TextInput("Deep focus target"), height=38))
        for index in range(depth):
            nested = bf.gui.CollapseContainer(f"Depth {depth - index}", bf.gui.Column(6), nested)
            nested.set_padding(4)
            nested.state.value = True
            self.collapses.append(nested)
        inner = bf.gui.ScrollingContainer(bf.gui.Column(8).set_child_constraints(bf.gui.FillX()), nested)
        inner.set_scroll_x_enabled(False).set_padding(8).add_constraints(bf.gui.Height(220))
        self.nested_scroll = inner
        return section("03 / Scrolling inside scrolling", horizontal, inner)

    def make_layouts(self):
        self.width_policy = bf.gui.Width(180.0)
        badge = label("Width animated by PropertyEaser").set_auto_wraplength(True)
        self.resize_box = column(badge).set_padding(10).add_constraints(self.width_policy, bf.gui.Height(80))
        self.width_easer = bf.PropertyEaser(duration=1.4, easing=bf.easing.EASE_IN_OUT, register=self.name)
        self.width_easer.add_attr(self.width_policy, "value", 420.0)
        free = bf.gui.Container(bf.gui.FreeLayout()).set_padding(8).add_constraints(bf.gui.Height(95))
        free.add(fixed(label("Top left"), 110, 28).add_constraints(bf.gui.AnchorTopLeft()),
                 fixed(label("Centered"), 110, 28).add_constraints(bf.gui.Anchor(bf.alignment.CENTER)),
                 fixed(label("Bottom right"), 130, 28).add_constraints(bf.gui.AnchorBottomRight()))
        grid = bf.gui.Container(bf.gui.GridFill(2, 3, 6),
                               *(bf.gui.Button(f"Cell {i + 1}") for i in range(6)))
        grid.add_constraints(bf.gui.Height(90))
        equal = bf.gui.Container(bf.gui.RowFill(6), *(label(t) for t in ("RowFill", "equal", "shares")))
        equal.add_constraints(bf.gui.Height(35))
        stacked = bf.gui.Container(bf.gui.ColumnFill(4), label("ColumnFill / upper"), label("lower"))
        stacked.add_constraints(bf.gui.Height(60))
        # A Row preserves the box's width policy; the surrounding Column fills.
        return section("04 / Constraints and allocation", free, grid, equal, stacked, row(self.resize_box),
                       bf.gui.Button("Animate preferred width", self.animate_width))

    def make_load(self):
        buttons = row(bf.gui.Button("Add 24 cards", lambda: self.add_cards(24)),
                      bf.gui.Button("Remove 24", self.remove_cards))
        return section("05 / Widget load bank", self.load_count, buttons, self.load_grid)

    def add_cards(self, count):
        for _ in range(count):
            index = len(self.load_grid.children)
            value = bf.gui.SyncedVar((index % 11) / 10.0)
            slider = fixed(bf.gui.Slider("", synced_var=value).set_step(.1), height=24)
            meter = fixed(bf.gui.BarMeter(0.0, 1.0, synced_var=value), height=8)
            card = column(label(f"Node {index + 1:03d}"), slider, meter,
                          bf.gui.Toggle("Active", default_value=index % 2 == 0), gap=5).set_padding(8)
            card.add_constraints(bf.gui.FillX())
            self.load_grid.add(card)
        self.load_count.set_text(f"{len(self.load_grid.children)} cards / independent value bindings")

    def remove_cards(self):
        # Deregister detached widgets so repeated add/remove stress does not
        # retain them in the global style manager.
        removed = self.load_grid.children[-24:]
        self.load_grid.remove(*removed)
        for card in removed:
            card.visit(bf.gui.StyleManager().remove_widget)
        self.load_count.set_text(f"{len(self.load_grid.children)} cards / independent value bindings")

    def retarget(self):
        self.pulse.properties[0].end_value = .1 if self.level.value > .5 else .9
        self.pulse.start(force=True)

    def animate_width(self):
        self.width_easer.properties[0].end_value = 180.0 if self.width_policy.value > 300 else 420.0
        self.width_easer.start(force=True)

    def reset_scroll(self):
        self.root.visit(lambda w: w.reset_scroll() if isinstance(w, bf.gui.Container) else None)

    def toggle_collapses(self):
        expanded = not all(w.state.value for w in self.collapses)
        for widget in self.collapses:
            widget.state.value = expanded

    def toggle_debug(self):
        bf.Context.debug_mode = (bf.debugMode.HIDDEN if bf.Context.debug_mode == bf.debugMode.OUTLINES
                                 else bf.debugMode.OUTLINES)

    def do_early_handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_F1, pygame.K_ESCAPE):
            if event.key == pygame.K_F1:
                self.toggle_debug()
            else:
                self.manager.stop()
            event.consumed = True

    def update(self, dt):
        start = perf_counter()
        super().update(dt)
        self.last_update_ms = (perf_counter() - start) * 1000

    def draw(self, surface):
        start = perf_counter()
        super().draw(surface)
        self.last_draw_ms = (perf_counter() - start) * 1000
        self.frame_samples.append(self.last_update_ms + self.last_draw_ms)

    def do_update(self, dt):
        self.elapsed += dt
        self.frames += 1
        if self.animate.value and self.pulse.is_stopped:
            self.retarget()
        if self.elapsed - self.last_report >= .25:
            self.last_report = self.elapsed
            nodes = []
            self.root.visit(nodes.append)
            self.status.set_text(f"{len(nodes)} widgets   |   update {self.last_update_ms:.1f} ms   "
                                 f"draw {self.last_draw_ms:.1f} ms   |   F1 outlines   Esc exit")

    def exercise(self, frame):
        """Deterministic scripted stress, also available in a visible window."""
        if frame % 45 == 0:
            sizes = ((1280, 860), (880, 640), (1440, 900), (640, 480))
            width, height = sizes[(frame // 45) % len(sizes)]
            self.manager.process_event(pygame.Event(pygame.VIDEORESIZE, w=width, h=height, size=(width, height)))
            self.toggle_collapses()
            self.selector.set_by_index((frame // 45) % 3)
            self.message.value = f"Frame {frame}: " + "wrapping / cursor / binding " * 8
            self.animate_width()
        if frame % 60 == 10:
            self.add_cards(24)
        if frame % 60 == 40:
            self.remove_cards()
        if frame % 45 == 15:
            self.dropdown.open()
        if frame % 45 == 30:
            self.dropdown.close()
        for viewport in (self.gallery, self.nested_scroll):
            extent = max(0, viewport.layout.children_rect.h - viewport.get_inner_height())
            viewport.set_scroll((0, extent * (.5 + .5 * math.sin(frame / 25))))

    def validate(self):
        """Fail a scripted run if layout produces invalid or clipped thumbs."""
        def check(widget):
            assert all(math.isfinite(v) for v in widget.rect), f"Nonfinite rect: {widget}"
            assert widget.rect.w >= 0 and widget.rect.h >= 0, f"Negative size: {widget}"
            if isinstance(widget, bf.gui.ScrollingContainer):
                for track in (widget.h_track, widget.v_track):
                    if not track.visible:
                        continue
                    thumb, rail = track.handle.rect, track.get_inner_rect()
                    assert track.handle.visible, f"Hidden thumb: {widget}"
                    assert (thumb.left >= rail.left - .001 and thumb.top >= rail.top - .001
                            and thumb.right <= rail.right + .001 and thumb.bottom <= rail.bottom + .001), \
                        f"Thumb outside rail: {thumb} / {rail}"
        self.root.visit(check)
        assert all(entry.text == self.message.value for entry in self.inputs), "Text bindings diverged"
        assert self.dropdown.get_current_value() == self.choice.value, "Dropdown binding diverged"
        assert self.selector.options[self.selector.get_current_index()] == self.choice.value, "Selector binding diverged"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cards", type=int, default=48, help="Initial load-bank cards (default: 48)")
    parser.add_argument("--depth", type=int, default=6, help="Nested collapsible panels (default: 6)")
    parser.add_argument("--headless", action="store_true", help="Use SDL dummy video/audio")
    parser.add_argument("--frames", type=int, default=0, help="Exit after N frames; headless defaults to 180")
    parser.add_argument("--exercise", action="store_true", help="Automatically resize, scroll and change content")
    parser.add_argument("--screenshot", type=Path, help="Save the final frame as a PNG")
    parser.add_argument(
        "--profile", nargs="?", const=Path("gui-stress.prof"), type=Path,
        help="Write cProfile stats to PATH (default: gui-stress.prof) and print the top callers",
    )
    args = parser.parse_args()
    if min(args.cards, args.depth, args.frames) < 0:
        parser.error("cards, depth and frames must be non-negative")
    logging.getLogger().setLevel(logging.WARNING)
    pygame.init()
    bf.init((1600,900), window_caption="batFramework / GUI stress laboratory",
            default_font_size=16, fps_limit=60, flags=pygame.SCALED)
    # bf.FontManager().set_default_antialias(True)
    # Register before constructing the scene. New cards and dropdown options
    # receive these styles through WidgetMeta, with no manual tree traversal.
    styles = bf.gui.StyleManager()
    styles.add(StressStyle())
    styles.add(StressCompositeStyle())
    # SDL's dummy driver cannot create system cursors. This only affects the
    # optional headless run; visible runs exercise the real pointer behavior.
    if args.headless:
        from unittest.mock import patch
        cursor_context = patch("pygame.mouse.set_cursor")
    else:
        cursor_context = nullcontext()
    try:
        with cursor_context:
            scene = GuiStressDemo(args.cards, args.depth)
            manager = bf.Manager(scene)
            manager.running = True
            limit = args.frames or (180 if args.headless else 0)
            clock = manager.clock
            frame = 0
            profiler = cProfile.Profile() if args.profile else None
            if profiler:
                profiler.enable()
            try:
                while manager.running and (not limit or frame < limit):
                    for event in pygame.event.get():
                        manager.process_event(event)
                    if args.exercise:
                        scene.exercise(frame)
                    dt = 1 / 60 if args.headless else min(clock.tick(60) / 1000, .1)
                    manager.update(dt)
                    if args.headless or args.exercise:
                        scene.validate()
                    manager.draw(bf.const.SCREEN)
                    pygame.display.flip()
                    frame += 1
            finally:
                if profiler:
                    profiler.disable()
                    profiler.dump_stats(str(args.profile))
                    summary = io.StringIO()
                    pstats.Stats(profiler, stream=summary).sort_stats("cumulative").print_stats(25)
                    print(f"Profile written to {args.profile}")
                    print(summary.getvalue(), end="")
            if args.screenshot:
                pygame.image.save(bf.const.SCREEN, str(args.screenshot))
            samples = sorted(scene.frame_samples)
            if samples:
                nodes = []
                scene.root.visit(nodes.append)
                print(f"{frame} frames; {len(nodes)} widgets; update + draw (last {len(samples)} frames): "
                      f"mean {sum(samples) / len(samples):.2f} ms, "
                      f"p95 {samples[min(len(samples) - 1, int(len(samples) * .95))]:.2f} ms")
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()

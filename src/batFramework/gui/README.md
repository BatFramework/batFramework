# GUI layout

Layout has two phases, followed by painting:

```python
root.measure((800, 600))
root.arrange((0, 0, 800, 600))
root.paint_tree()
```

`Root.update_tree()` runs these steps automatically using the root's current
size. It also handles separate popup and tooltip layout passes, described below.
There is no repeated whole-tree constraint solver.

## Measurement

`widget.measure(available_size)` receives the **maximum outer size** the parent
offers. It returns and stores `widget.desired_size`. It does not resize or move
rectangles, allocate surfaces, or paint. Desired sizes travel back up the tree.
Padding and relief are included in the desired outer size and subtracted before
offering space to children.

`set_size()` records a preferred size separately from the arranged rectangle.
With autoresize disabled, that request is used instead of intrinsic content size.
Shrinking a widget therefore does not destroy its original request. Minimum
sizes are preferences: the parent's maximum always wins if space is insufficient.

Size constraints calculate preferences without changing autoresize flags.
Higher priorities run last; equal priorities follow insertion order. Ordinary
percentages use the child's offered space. `PercentageRectWidth` and
`PercentageRectHeight` use the parent's proposed outer size, still bounded by
the offer. On an infinite axis, fill and nonzero percentages fall back to the
intrinsic preference.

## Arrangement

`widget.arrange(final_rect)` accepts either `(width, height)` at the current
position or `(x, y, width, height)` in world coordinates. It assigns the exact
outer size. The child must accept that allocation, even if smaller than its
desired or minimum size. Position constraints calculate placement from that
allocation and the parent's final bounds. `arrange()` commits the resulting
position once, then arranges descendants. Surfaces are painted only after
geometry is complete.

Anchors use the parent's content viewport (including padding, relief, and
scrollbar reservations). Pixel and percentage margins use that same viewport;
rectangle-relative percentages use the parent's outer box. Position policies
run in priority order, with later insertion winning ties. They cannot resize
the child. Within a single `Margin(left, top, right, bottom)`, right wins over
left and bottom wins over top when both edges are specified. Unspecified axes
keep the layout's placement; negative margins are allowed. Position policies
can override a row/grid slot's position and do not reserve additional space
during measurement.

Rows and columns offer space to nongrowing children first, in child order, then
offer weighted shares of the remainder to growers. `GrowH` and `GrowV` are
handled by the matching parent layout; they never resize siblings themselves.
At arrangement, growers receive their weighted shares subject to their size
policies. Space left unused by a maximum-size policy is not redistributed.
Fill rows/columns divide the available main axis evenly. Grids offer equal cell
limits; `GridFill` assigns the complete cells. Empty layouts request zero content
space. Explicitly hidden widgets retain their layout slots; `CollapseContainer`
handles collapsing its content explicitly.

`ScrollingContainer` offers infinity on enabled scrolling axes so content can
exceed the viewport. Disable horizontal scrolling to wrap text to the viewport
width. Measurement accounts for the space occupied by scrollbars, with at most
three local measurements as bars become necessary. If the final allocation
differs from the measured offer, the viewport is measured again before any
descendants are arranged. Descendants are arranged once after the viewport is
chosen. A regular container bounds its content; use `ScrollingContainer` for
overflow.

Scrollbars reuse `SliderMeter` and `SliderHandle`, with a proportional thumb
provided by `SliderMeter.get_handle_size(available_size)`. Style them through
`h_track`, `h_handle`, `v_track`, and `v_handle`; each handle is now a child of
its track. Scrollbar visibility is committed during arrangement and does not
drive viewport sizing. Disabling an axis resets its offset. `clear_children()`
preserves the scrollbars. Wheel input retains its magnitude, Shift redirects
vertical wheel input horizontally, and events bubble when scrolling cannot
move further. Dragging or clicking a scrollbar preserves keyboard focus.

## Dropdown layout

Option rows measure their text naturally. They stretch to the panel's content
width only during arrangement; using `FillX` during measurement would instead
make them request the entire offered screen width.

Opening a dropdown registers its panel with
`Root.attach_to_layer(..., layout_callback=panel.layout_popup)`. The root excludes
registered popups from normal child layout. After the regular UI has its final
rectangles, the root calls each popup's layout callback with the camera's visible
world rectangle. Hover resolution, tooltip layout, and painting follow this pass.

The dropdown panel first measures within the viewport to find its preferred
size. Its allocated width is at least the button width, may grow for wider
options, and never exceeds the viewport's safe width. It prefers the space below
the button, flips above when that fits better, and otherwise uses the larger
side. It remeasures within the chosen width and height to account for wrapping
and scrollbars, clamps its position to the viewport, and arranges once.

The panel reuses `ScrollingContainer` with horizontal scrolling disabled. Long
lists scroll vertically; opening or changing the selection reveals the selected
row. Configure placement through `dropdown.panel_gap` (4),
`dropdown.panel_screen_margin` (4), and `dropdown.panel_max_height` (320).
Access `dropdown.panel` to style its background and existing scrollbar widgets.

Option buttons exist immediately after construction and register automatically
with `StyleManager`, just like other widgets. Register a `Style` subclass with
`StyleManager().add(style)` and put option appearance in its `apply(widget)`
method (option rows are `Button` instances). Rows created by later `set_options()`
calls receive the same registered styles automatically. Styles can also access
`dropdown.panel` to customize the popup. The stress demo registers basic widget
rules followed by composite rules, so child visuals keep their specific styling
when the manager reapplies the theme. The overlay receives mouse hits before normal content;
selection, Escape, outside clicks, and removing the dropdown close its panel.

## Tooltip layout

The root excludes its tooltip from ordinary child measurement and arrangement.
`Root.update_tree()` first measures and arranges the regular UI and open popups,
then resolves hover against the final rectangles and calls `ToolTip.set_target()`. The tooltip
updates its text and delay/fade state without changing geometry. Pending delays
are cancelled when the target disappears or tooltips are disabled.

If the tooltip is visible (including while fading out), the root offers at most
`tooltip.max_width` (320 by default) and the available viewport height. Inherited
`Label.measure()` wraps text within that offer and returns `desired_size`.
The root positions that size beside the pointer, flips at edges, clamps it to
the camera's visible world rectangle inset by `tooltip.screen_margin` (4 by
default), and calls `tooltip.arrange(rect)` once. Tiny viewports bound both
dimensions; text taller than the available height is clipped. All placement
uses GUI world coordinates. The entire tree is painted only after this step.

The tooltip remains attached to the root's tooltip draw layer and never takes
mouse hits. Its delay and fade timers are reusable and use the scene's timer
register. Direct `root.measure()` / `root.arrange()` calls cover the regular UI;
use `root.update_tree()` to include popup layout, hover resolution, and tooltip layout.

## Custom widgets and constraints

For a leaf, override `get_min_required_size()` to return its intrinsic outer
size. For a composite, override `measure_override(content_available_size)`:
measure children with their limits and return your preferred **outer** size.
Do not read child rectangles as measurement results; use their `desired_size`.

Override `arrange_override()` to position local visuals and assign child
rectangles with `child.arrange()`. A composite should arrange each child once.
`arrange_children(exclude=(...))` arranges any additional children while skipping
the composite's own slots. The parent allocation is final throughout this hook.
Text inputs update cursor visibility here, before painting.

`paint_tree()` visits children first, then paints a widget if `needs_paint()`
returns true. The default checks visibility and `dirty_surface`; labels also
check whether their renderer or text effect is dynamic. Override `paint()` for
drawing and `needs_paint()` for custom repaint policies. Geometry belongs in
measurement and arrangement, never in painting. Root participates in traversal
but does not paint its own surface.

Layout is measured and arranged on every tree update. `dirty_surface` is the
only invalidation flag: use it when a content or style change needs repainting.

Custom size constraints must implement the pure hook:

```python
class HalfHeight(Constraint):
    def __init__(self):
        super().__init__()
        self.affects_size = True

    def constrain_size(self, child_widget, preferred, available):
        return preferred[0], available[1] / 2
```

Custom position constraints implement a rectangle-only hook. Inputs are world
coordinates; return a new rectangle with the same size and finite coordinates,
without mutating any input:

```python
class TopCenter(Constraint):
    def __init__(self):
        super().__init__()
        self.affects_position = True

    def constrain_position(self, proposed_rect, parent_rect, parent_inner_rect):
        result = proposed_rect.copy()
        result.midtop = parent_inner_rect.midtop
        return result
```

`Widget.constrain_position(proposed_rect)` composes position policies without
changing geometry. `arrange()` uses it directly. Constraint objects expose only
the pure sizing/positioning hooks; they do not evaluate and mutate widgets in a
separate solver. There are no compatibility update passes. Subclasses should
use the measurement, arrangement, and painting hooks described above.

## Verification

From the repository root, with pygame-ce installed:

```console
python -m unittest discover -s tests -v
```

The tests use SDL's dummy display and exercise geometry, nesting, size changes,
constraints, scrolling, wrapping, and painting composite controls.

from .label import Label
import batFramework as bf
import sys
from typing import Self

class ToolTip(Label):
    """Label with delayed visibility; Root owns its measurement and placement."""

    def __init__(self, text=""):
        super().__init__(text)

        self.fade_in_duration: float = 0.1
        self.fade_out_duration: float = 0.1
        self.offset_scale: float = 4
        self.max_width: float = 320
        self.screen_margin: float = 4
        self.target = None
        self.set_auto_wraplength(True)

    def set_offset_scale(self, scale: float) -> Self:
        self.offset_scale = scale
        return self

    def do_when_added(self):
        if r:=self.get_root():
            r.attach_to_layer(self, bf.gui.GuiLayer.TOOLTIP)

        self.fade_in_easer = bf.PropertyEaser(
            duration=self.fade_in_duration,
            easing=bf.easing.EASE_OUT,
            loop=0,
            register=self.parent_scene.name,
        ).add_custom(self.get_alpha, self.set_alpha, 255).set_auto_delete(False)

        self.fade_out_easer = bf.PropertyEaser(
            duration=self.fade_out_duration,
            easing=bf.easing.EASE_IN,
            loop=0,
            register=self.parent_scene.name,
            end_callback=lambda: self.set_visible(False),
        ).add_custom(self.get_alpha, self.set_alpha, 0).set_auto_delete(False)

        self.delay_timer = bf.Timer(0.5, self._fade_in_internal, 0,
                                   register=self.parent_scene.name).set_auto_delete(False)

        self.set_draw_order(sys.maxsize)
        self.set_padding((4, 2))
        self.set_visible(False)
        self.set_alpha(0)



    def __str__(self):
        return f"ToolTip('{self.text}')"

    def top_at(self, x, y):
        return None  # Tooltips should not block mouse

    def set_target(self, target) -> Self:
        """Update content and appearance state; never change layout geometry."""
        if target is not None:
            self.set_text(target.tooltip_text)
        if target is self.target:
            return self
        self.target = target
        if target is None:
            self.fade_out()
        else:
            self.fade_in()
        return self

    # -----------------------------------------
    # Fade Logic
    # -----------------------------------------

    def set_fade_in_delay(self, delay : float) -> Self:
        self.delay_timer.set_duration(delay)
        return self

    def _fade_in_internal(self):
        # If we got disabled or lost target during delay, abort
        root = self.get_root()
        if self.target is None or root is None or not root.show_tooltip:
            return

        if not self.visible:
            self.set_visible(True)

        if self.fade_in_easer.has_started() and not self.fade_in_easer.is_stopped:
            return

        self.fade_out_easer.stop()
        self.fade_in_easer.start()

    def fade_in(self):
        """Trigger fading in after tooltip delay"""
        self.delay_timer.stop()
        self.fade_out_easer.stop()
        if self.visible:
            # Retargeting a visible tooltip should not blink or finish fading out.
            self._fade_in_internal()
        else:
            self.delay_timer.start(force=True)

    def fade_out(self):
        """Hide tooltip and cancel any pending delayed fade-in."""
        # Cancel any pending delayed fade-in *completely*
        self.delay_timer.stop()

        # If already invisible and alpha is 0, no need to do anything
        if not self.visible and self.get_alpha() <= 0:
            return self

        # Don't restart if already fading out
        if self.fade_out_easer.has_started() and not self.fade_out_easer.is_stopped:
            return self

        # Stop any ongoing fade in
        self.fade_in_easer.stop()
        self.fade_out_easer.start()
        return self

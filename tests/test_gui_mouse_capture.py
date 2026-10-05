"""Mouse button changes after a press leaves a widget."""

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pygame
import batFramework as bf


class ClickProbe(bf.gui.InteractiveWidget):
    def __init__(self):
        super().__init__()
        self.clicks = []

    def do_on_click_down(self, button, event=None):
        self.clicks.append(("down", button))

    def do_on_click_up(self, button, event=None):
        self.clicks.append(("up", button))


class DragProbe(bf.gui.DraggableWidget):
    def __init__(self):
        super().__init__()
        self.clicks = []
        self.moves = []

    def do_on_click_down(self, button, event=None):
        self.clicks.append(("down", button))

    def do_on_click_up(self, button, event=None):
        self.clicks.append(("up", button))

    def do_on_drag(self, start, end):
        self.moves.append((start, end))


class MouseCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((100, 100))

    def test_release_outside_calls_up_once(self):
        buttons = [True, False, False, False, False]
        widget = ClickProbe()
        widget.is_hovered = True
        with patch("pygame.mouse.get_pressed", side_effect=lambda count=3: tuple(buttons[:count])), \
                patch("pygame.mouse.get_pos", return_value=(90, 90)):
            widget.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, consumed=False))
            widget.on_exit()
            buttons[0] = False
            widget.update(0)
            widget.update(0)
        self.assertEqual(widget.clicks, [("down", 1), ("up", 1)])
        self.assertFalse(any(widget.is_clicked_down))

    def test_masked_buttons_share_one_drag_and_keep_each_click_hook(self):
        buttons = [True, False, False, False, False]
        widget = DragProbe()
        widget.set_click_mask(1, 0, 1)
        widget.get_camera = Mock(return_value=Mock(get_mouse_pos=Mock(return_value=(10, 10))))
        widget.is_hovered = True
        with patch("pygame.mouse.get_pressed", side_effect=lambda count=3: tuple(buttons[:count])), \
                patch("pygame.mouse.get_pos", return_value=(10, 10)):
            widget.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, consumed=False))
            widget.on_exit()
            widget.update(0)
            first_start = widget.drag_start
            self.assertTrue(widget.is_dragged)

            buttons[2] = True
            widget.update(0)
            self.assertTrue(widget.is_dragged)
            self.assertEqual(widget.drag_start, first_start)

            buttons[0] = False
            widget.update(0)
            self.assertTrue(widget.is_dragged)
            self.assertEqual(widget.drag_start, first_start)

            buttons[2] = False
            widget.update(0)
            self.assertFalse(widget.is_dragged)
            self.assertIsNone(widget.drag_start)

        self.assertEqual(widget.clicks, [("down", 1), ("down", 3), ("up", 1), ("up", 3)])
        self.assertGreaterEqual(len(widget.moves), 2)

    def test_same_frame_button_events_are_not_hidden_by_pressed_snapshot(self):
        buttons = [True, False, True, False, False]
        widget = DragProbe()
        widget.set_click_mask(1, 0, 1)
        widget.is_hovered = True
        with patch("pygame.mouse.get_pressed", side_effect=lambda count=3: tuple(buttons[:count])):
            widget.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, consumed=False))
            widget.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, consumed=False))
        self.assertEqual(widget.clicks, [("down", 1), ("down", 3)])
        self.assertTrue(widget.is_dragged)

    def test_unmasked_button_still_gets_its_release_after_drag_ends(self):
        buttons = [True, True, False, False, False]
        widget = DragProbe()
        widget.set_click_mask(1)
        widget.get_camera = Mock(return_value=Mock(get_mouse_pos=Mock(return_value=(10, 10))))
        widget.is_hovered = True
        with patch("pygame.mouse.get_pressed", side_effect=lambda count=3: tuple(buttons[:count])), \
                patch("pygame.mouse.get_pos", return_value=(10, 10)):
            widget.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, consumed=False))
            widget.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=2, consumed=False))
            widget.on_exit()
            widget.update(0)
            buttons[0] = False
            widget.update(0)
            self.assertFalse(widget.is_dragged)
            buttons[1] = False
            widget.update(0)
        self.assertEqual(widget.clicks, [("down", 1), ("down", 2), ("up", 1), ("up", 2)])

    def test_forwarded_drag_press_is_tracked(self):
        buttons = [True, False, False, False, False]
        widget = DragProbe()
        with patch("pygame.mouse.get_pressed", side_effect=lambda count=3: tuple(buttons[:count])), \
                patch("pygame.mouse.get_pos", return_value=(90, 90)):
            widget.on_click_down(1, pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, consumed=False))
            buttons[0] = False
            widget.update(0)
        self.assertEqual(widget.clicks, [("down", 1), ("up", 1)])

    def test_slider_handle_keeps_drag_when_hover_ends(self):
        buttons = [True, False, False, False, False]
        handle = bf.gui.Slider("Volume").meter.handle
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, consumed=False)
        with patch("pygame.mouse.get_pressed", side_effect=lambda count=3: tuple(buttons[:count])), \
                patch("pygame.mouse.set_cursor"):
            handle.on_click_down(1, event)
            handle.on_exit()
            self.assertTrue(handle.is_clicked_down[0])
            self.assertTrue(handle.is_dragged)
            buttons[0] = False
            handle.update(0)
        self.assertFalse(handle.is_dragged)
        self.assertFalse(handle.is_clicked_down[0])

    def test_other_widgets_do_not_activate_from_captured_press(self):
        buttons = [False, True, False, False, False]
        clicks = []
        button = bf.gui.ClickableWidget(lambda: clicks.append("clicked"))
        button.ask_focus = Mock(return_value=True)
        button.is_hovered = True
        with patch("pygame.mouse.get_pressed", side_effect=lambda count=3: tuple(buttons[:count])), \
                patch("pygame.mouse.get_pos", return_value=(90, 90)), \
                patch("pygame.mouse.set_cursor"):
            button.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=2, consumed=False))
            button.on_exit()
            buttons[0] = True
            button.update(0)
            self.assertFalse(button.is_pressed)
            buttons[0] = False
            button.update(0)
            buttons[1] = False
            button.update(0)
        self.assertEqual(clicks, [])

        captured = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                      consumed=False, synthetic_capture=True)
        entry = bf.gui.TextInput("hello")
        entry.ask_focus = Mock()
        entry._place_cursor_from_mouse = Mock()
        entry.on_click_down(1, captured)
        entry.ask_focus.assert_not_called()
        entry._place_cursor_from_mouse.assert_not_called()

        root = bf.gui.Root()
        root.clear_focused = Mock()
        root.on_click_down(1, captured)
        root.clear_focused.assert_not_called()

    def test_regular_button_click_still_activates(self):
        clicks = []
        button = bf.gui.ClickableWidget(lambda: clicks.append("clicked"))
        button.ask_focus = Mock(return_value=True)
        with patch("pygame.mouse.set_cursor"):
            button.on_click_down(1, pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, button=1, consumed=False))
            button.on_click_up(1, pygame.event.Event(
                pygame.MOUSEBUTTONUP, button=1, consumed=False))
        self.assertEqual(clicks, ["clicked"])


if __name__ == "__main__":
    unittest.main()

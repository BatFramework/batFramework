import pygame
import batFramework as bf
from .widget import Widget
from .textWidget import TextWidget
from .textBuffer import TextBuffer




class TextInput(Widget):
    def __init__(self, text: str = ""):
        super().__init__()
        self.buffer = TextBuffer(text)

        self.line_widgets = []
        self.font_size = bf.FontManager().DEFAULT_FONT_SIZE
        self.font = bf.FontManager().get_font(None, self.font_size)

        self.cursor_visible = True
        self.cursor_timer = 0.0
        self.cursor_blink_rate = 0.5

        self.set_autoresize(True)

    # ------------------------------------------
    # INPUT HANDLING
    # ------------------------------------------

    def handle_event(self, event):
        super().handle_event(event)
        if event.consumed : return

        if event.type not in [pygame.KEYDOWN, pygame.TEXTINPUT]:
            return
        if event.type == pygame.TEXTINPUT:
            self.buffer.insert_char(event.text)
            self.dirty_shape = True
            event.consumed= True
            return
        
        k = event.key

        if k == pygame.K_BACKSPACE:
            self.buffer.backspace()

        elif k == pygame.K_DELETE:
            self.buffer.delete()

        elif k == pygame.K_RETURN:
            self.buffer.insert_newline()

        elif k == pygame.K_LEFT:
            self.buffer.move_left()

        elif k == pygame.K_RIGHT:
            self.buffer.move_right()

        elif k == pygame.K_UP:
            self.buffer.move_up()

        elif k == pygame.K_DOWN:
            self.buffer.move_down()

        else:
            return
        event.consumed = True
        self.dirty_shape = True

    # ------------------------------------------
    # INTERNAL RENDERING
    # ------------------------------------------

    def _ensure_line_widgets(self):
        needed = len(self.buffer.lines)
        current = len(self.line_widgets)

        if needed > current:
            for _ in range(needed - current):
                w = TextWidget("")
                w.set_font(force=True)
                self.add(w)
                self.line_widgets.append(w)

        elif needed < current:
            for w in self.line_widgets[needed:]:
                self.remove(w)
            self.line_widgets = self.line_widgets[:needed]

    def build(self):
        self._ensure_line_widgets()

        max_w = 0
        total_h = 0

        for i, line in enumerate(self.buffer.lines):
            self.line_widgets[i].set_text(line)
            self.line_widgets[i].build()
            w, h = self.line_widgets[i].rect.size
            max_w = max(max_w, w)
            total_h += h

        target = self.resolve_size((max_w, total_h))
        if self.rect.size != target:
            self.set_size(target)
            return True
        return False

    def paint(self):
        self._resize_surface()
        self.surface.fill((255, 255, 255))

        y = 0
        cursor_rect = None

        for i, w in enumerate(self.line_widgets):
            h = w.rect.height

            # paint the line into our main surface
            w.paint()
            self.surface.blit(w.surface, (0, y))

            if i == self.buffer.cursor_y:
                cursor_x_px = self.font.size(w.text[:self.buffer.cursor_x])[0]

                cursor_rect = pygame.Rect(cursor_x_px, y, 2, h)

            y += h

        # blinking cursor
        if cursor_rect and self.cursor_visible:
            pygame.draw.rect(self.surface, (0, 0, 0), cursor_rect)

    def update(self, dt):
        self.cursor_timer += dt
        if self.cursor_timer >= self.cursor_blink_rate:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
            self.dirty_surface = True

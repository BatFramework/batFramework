
class TextBuffer:
    def __init__(self, text: str = ""):
        self.lines = text.split("\n") if text else [""]
        self.cursor_x = 0
        self.cursor_y = 0

    # --- Internal helpers -------------------------------------
    def _clamp_cursor(self):
        self.cursor_y = max(0, min(self.cursor_y, len(self.lines) - 1))
        line_len = len(self.lines[self.cursor_y])
        self.cursor_x = max(0, min(self.cursor_x, line_len))

    # --- Cursor movement ---------------------------------------
    def move_left(self):
        if self.cursor_x > 0:
            self.cursor_x -= 1
        else:
            if self.cursor_y > 0:
                self.cursor_y -= 1
                self.cursor_x = len(self.lines[self.cursor_y])

    def move_right(self):
        if self.cursor_x < len(self.lines[self.cursor_y]):
            self.cursor_x += 1
        else:
            if self.cursor_y < len(self.lines) - 1:
                self.cursor_y += 1
                self.cursor_x = 0

    def move_up(self):
        self.cursor_y -= 1
        self._clamp_cursor()

    def move_down(self):
        self.cursor_y += 1
        self._clamp_cursor()

    # --- Modification ------------------------------------------
    def insert_char(self, ch: str):
        line = self.lines[self.cursor_y]
        self.lines[self.cursor_y] = line[:self.cursor_x] + ch + line[self.cursor_x:]
        self.cursor_x += len(ch)

    def backspace(self):
        if self.cursor_x > 0:
            line = self.lines[self.cursor_y]
            self.lines[self.cursor_y] = line[:self.cursor_x-1] + line[self.cursor_x:]
            self.cursor_x -= 1
        else:
            if self.cursor_y > 0:
                prev_line_len = len(self.lines[self.cursor_y-1])
                self.lines[self.cursor_y-1] += self.lines[self.cursor_y]
                self.lines.pop(self.cursor_y)
                self.cursor_y -= 1
                self.cursor_x = prev_line_len

    def delete(self):
        line = self.lines[self.cursor_y]
        if self.cursor_x < len(line):
            self.lines[self.cursor_y] = line[:self.cursor_x] + line[self.cursor_x+1:]
        else:
            if self.cursor_y < len(self.lines) - 1:
                self.lines[self.cursor_y] += self.lines[self.cursor_y+1]
                self.lines.pop(self.cursor_y + 1)

    def insert_newline(self):
        line = self.lines[self.cursor_y]
        before = line[:self.cursor_x]
        after = line[self.cursor_x:]
        self.lines[self.cursor_y] = before
        self.lines.insert(self.cursor_y+1, after)
        self.cursor_y += 1
        self.cursor_x = 0

    # --- Export -------------------------------------------------
    def get_text(self):
        return "\n".join(self.lines)

import batFramework as bf
import pygame
from math import sin
from .container import Container


class Indicator(bf.Entity):
    def __init__(self) -> None:
        super().__init__((10,10),convert_alpha=True)
        self.set_visible(False)
        self.surface.fill((0,0,0,0))
        p2 = (0,0)
        p1 = (p2[0] + 4, p2[1] + 4)
        p0 = (p2[0], p2[1] + 8)

        self.double_surf = self.surface.copy()
        pygame.draw.polygon(self.surface, bf.color.LIGHT_GB, [p0, p1, p2])
        pygame.draw.polygon(self.surface, bf.color.LIGHT_GB, [p0, p1, p2])
        self.anchor = 0,0
        self.anim = bf.EasingAnimation(loop=True,update_callback=lambda x,self=self: self.set_position(self.anchor[0]+(0.2* sin(pygame.time.get_ticks() * 0.008)),self.anchor[1]))
        self.anim.start()

    def set_double(self,val:bool):
        self.double_surf = val

    def set_position(self, x, y):
        self.anchor = (x,y)
        return super().set_position(x, y)
class TextBox(Container):
    def __init__(self, uid=None):
        super().__init__(uid)
        self.messages = []
        self.message_length = None
        self.progression = 0
        self.click_rate, self.click_counter = 2, 0
        self.label = bf.Label("").set_alignment(bf.Alignment.LEFT).put_to(self)
        self.text_speed = 30
        self.end_callback = None
        self.indicator = Indicator()

    def set_position(self, x, y):
        val = super().set_position(x, y)        
        self.indicator.set_position(*self.rect.move(-12,-12).bottomright)
        return val
    def set_speed(self, speed=0):
        self.text_speed = max(0, min(speed, 100))

    def get_bounding_box(self):
        yield from super().get_bounding_box()
        yield from self.label.get_bounding_box()

    def resize(self, new_width, new_height):
        self.label.set_wraplength(
            int(self.rect.w - self.label._padding[0] - self._padding[0])
        )
        # print(f"wraplength set to {self.label._wraplength}")
        return super().resize(new_width, new_height)

    def string_too_wide(self, font: pygame.Font, string: str):
        width = font.size(string)[0] + self.label._padding[0] * 2

        return width >= self.rect.w - self._padding[0] * 2

    def queue_message(self, message: str, end_callback=None):
        # print("Queue message !",repr(message))
        self.end_callback = end_callback
        cut = None
        # self.label.set_text(message)
        font = bf.utils.FONTS[self.label._text_size]
        new_lines = [0]
        line_size = font.get_linesize()
        max_new_lines = (self.rect.h - self._padding[1] * 2) // (line_size)
        while len(new_lines) < max_new_lines + 1:
            # print(f"Max lines : {max_new_lines}, current new_lines : {new_lines}")
            reached_end = False
            next_new_line = new_lines[-1]
            last_index_is_space = True
            tmp_new_line = next_new_line
            while not reached_end:
                next_sp = message.find(" ", next_new_line + 1)
                next_n = message.find("\n", next_new_line + 1)
                if next_sp >= 0 and next_n >= 0:
                    tmp_new_line = min(next_sp, next_n)
                    if next_sp != tmp_new_line:
                        last_index_is_space = False
                        new_lines.append(tmp_new_line + 1)

                elif next_n >= 0:
                    tmp_new_line = next_n
                    new_lines.append(tmp_new_line + 1)

                    last_index_is_space = False
                elif next_sp >= 0:
                    tmp_new_line = next_sp
                else:
                    reached_end = True

                # print(next_sp,next_n,last_index_is_space,new_lines)

                if self.string_too_wide(
                    font,
                    message[
                        new_lines[-1] : (
                            tmp_new_line if not reached_end else len(message) - 1
                        )
                    ],
                ):
                    # print(f"last newline at {next_new_line} : ",repr(message[next_new_line]))
                    if last_index_is_space:
                        # print(f"{repr(message[new_lines[-1]:(tmp_new_line if not reached_end else len(message)-1)])} too long, cut at last available index {next_new_line if not reached_end else len(message)-1}")
                        message = (
                            message[:next_new_line]
                            + "\n"
                            + message[next_new_line + 1 :]
                        )
                    break

                last_index_is_space = True
                next_new_line = tmp_new_line

            new_lines.append(next_new_line + 1)
            if reached_end:
                break
        if len(new_lines) > max_new_lines:
            # print(f"Too many lines ->{new_lines}, cut at : ", new_lines[-2])
            message, cut = (
                message[: new_lines[-2]].strip(),
                message[new_lines[-2] :].strip(),
            )
            # print("Cut result -> message : ", repr(message), "cut :", repr(cut))
        # print("Final message :", repr(message))
        self.messages.append(message)

        # IF this is the first message
        if len(self.messages) == 1:
            self.progression = 0
            self.message_length = len(self.messages[0])
            # self.set_visible(True)
        if cut:
            self.queue_message(cut, end_callback)

    def next_message(self):
        self.indicator.set_visible(False)
        if self.progression != self.message_length:
            return
        self.messages.pop(0)
        self.progression = 0
        self.click_counter = 0
        self.message_length = len(self.messages[0]) if self.messages else None

        if self.message_length is None:
            if self.end_callback:
                self.end_callback()
            return

    def update(self, dt: float):
        self.indicator.update(dt)
        if not self.messages:
            return
        new_progression = min(
            self.progression + (dt * self.text_speed), self.message_length
        )


        if int(new_progression) != int(self.progression):
            if self.click_counter % self.click_rate == 0:
                bf.AudioManager().play_sound("text_click", 0.5)
            self.click_counter += 1

        self.label.set_text(self.messages[0][: int(new_progression)])
        self.progression = new_progression

        if self.progression == self.message_length:
            self.indicator.set_visible(True)
        else:
            self.indicator.set_visible(False)

    def draw(self, camera):
        i= super().draw(camera)
        i+=self.indicator.draw(camera)
        return i


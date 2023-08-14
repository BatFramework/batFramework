from custom_scenes import CustomBaseScene
import batFramework as bf
import pygame


class CharacterNotDefinedException(Exception):
    "Character not defined previously"
    pass


def custom_draw(self, camera, dimmer, func):
    i = bf.Entity.draw(self, camera)
    if i and func():
        camera.surface.blit(dimmer, (0, 0))
        i += 1
    return i


class DialogueScene(CustomBaseScene):
    def __init__(self) -> None:
        super().__init__("dialogue")
        self.text_box = bf.TextBox()
        self.text_box = bf.TextBox()
        text_box_height = 40
        self.text_box.resize(160, text_box_height)
        self.text_box.set_position(0, 144 - text_box_height)
        self.text_box.set_visible(False)

        self.background = bf.Image()
        self.character_sprite = bf.Image()
        self.current_character = None

        self.add_action(
            bf.Action("next").add_key_control(pygame.K_SPACE, pygame.K_RETURN)
        )

        self.add_hud_entity(self.background, self.character_sprite, self.text_box)
        self.control = True
        self.dimmer = pygame.Surface(self.hud_camera.rect.size).convert_alpha()
        self.dimmer.set_alpha(140)

        self.background.draw = lambda camera, dimmer=self.dimmer: custom_draw(
            self.background, camera, dimmer, self.is_character_on_screen
        )

    def do_when_added(self):
        self.update(0.1)

    def is_character_on_screen(self) -> bool:
        # print((not self.current_character is None),self.character_sprite.visible)
        return (not self.current_character is None) and self.character_sprite.visible

    def set_background(self, path, convert_alpha=False):
        if path is None:
            self.background.set_visible(False)
            return

        self.background.set_image(path, convert_alpha)
        self.background.set_visible(True)

    def give_control(self):
        self.control = True

    def take_control(self):
        self.control = False

    def show_textbox(self):
        self.text_box.set_visible(True)

    def hide_textbox(self):
        self.text_box.set_visible(False)

    def next_message(self):
        self.text_box.next_message()

    def say(
        self, message, character=None, emotion=None, facing_right=True, callback=None
    ):
        if character is not None and self.current_character is not None:
            if character is None and self.current_character and emotion:
                self.set_emotion(emotion)
            elif character and emotion:
                self.set_sprite(character, emotion)
            elif character:
                self.set_sprite(character, emotion)
            self.character_sprite.set_flip(not facing_right)
        # print(message)
        self.text_box.set_visible(True)
        self.text_box.queue_message(
            message, end_callback=lambda: [self.text_box.set_visible(False), callback()]
        )

    def set_sprite(self, character=None, emotion=None, facing_right=True):
        if not emotion:
            emotion = "neutral"
        if character is None:
            self.current_character = None
            self.character_sprite.set_visible(False)
            return
        self.current_character = character
        self.character_sprite.set_image(f"sprites/{character}/{emotion}.png", True)
        self.character_sprite.set_flip(not facing_right)
        self.character_sprite.set_visible(True)

    def set_emotion(self, emotion=None):
        if self.current_character is None:
            raise CharacterNotDefinedException
        else:
            if not emotion:
                emotion = "neutral"

            self.character_sprite.set_image(
                f"sprites/{self.current_character}/{emotion}.png", True
            )
        self.character_sprite.set_visible(True)

    def do_handle_event(self, event):
        if self.control and self._action_container.is_active("next"):
            self.next_message()

    def on_exit(self):
        self.current_character = None

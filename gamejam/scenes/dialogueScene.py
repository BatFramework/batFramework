from .custom_scenes import CustomBaseScene
import batFramework as bf
import pygame




class CharacterNotDefinedException(Exception):
    "Character not defined previously"
    pass





class DialogueScene(CustomBaseScene):
    def __init__(self) -> None:
        super().__init__("dialogue")
        self.set_clear_color((0,0,0,0))
        text_box_height = 40
        self.scene_textbox = bf.TextBox("dialogue_textbox")
        self.scene_textbox.resize(160, text_box_height)
        self.scene_textbox.set_position(0, 144 - text_box_height)
        self.scene_textbox.set_visible(False)


        self.dimmer = bf.Entity(self.hud_camera.rect.size,convert_alpha=True)
        self.dimmer.surface.fill((0,0,0))
        self.dimmer.set_visible(False)
        self.add_hud_entity(self.dimmer,self.scene_textbox)
        self.add_action(bf.Action("next").add_key_control(pygame.K_SPACE,pygame.K_RETURN))


    def on_enter(self):
        print("dialogue enter")
        self.manager._scenes[self.scene_index+1].set_active(True)
        self.manager._scenes[self.scene_index+1].set_visible(True)
        return super().on_enter()
    

    def fade_in(self,duration=300):
        self.dimmer.set_visible(True)
        bf.EasingAnimation("dimmer_fade_in",bf.Easing.EASE_IN_OUT,duration=duration,update_callback= lambda x : self.update_fade_alpha(x,"in")).start()

    def fade_out(self,duration=300):
        bf.EasingAnimation("dimmer_fade_in",bf.Easing.EASE_IN_OUT,duration=duration,update_callback= lambda x : self.update_fade_alpha(x,"out")).start()

    def update_fade_alpha(self,progression,state:str):
        if state == "in":
            self.dimmer.surface.set_alpha(int(140*progression))
        elif state == "out":
            self.dimmer.surface.set_alpha(140-int(140*progression))



    def on_exit(self):
        self.dimmer.set_visible(False)

        print("dialogue exit")
        return super().on_exit()

    def set_visible(self, value: bool):
        print("dialogue set visible",value)
        return super().set_visible(value)

    def show_textbox(self):
        self.scene_textbox.set_visible(True)

    def hide_textbox(self):
        self.scene_textbox.set_visible(False)

    def next_message(self):
        self.scene_textbox.next_message()

    def say(
        self, message, character=None, emotion=None, facing_right=None, callback=None
    ):
        # if character is not None or emotion is not None:
        #     match (character, emotion):
        #         case (None, e) if e is not None:
        #             self.set_emotion(e)
        #             if facing_right is not None:
        #                 self.character_sprite.set_flip(not facing_right)
        #         case (_, _):
        #             self.set_sprite(character, emotion,facing_right)
        # else:
        #     if facing_right is not None:
        #         self.character_sprite.set_flip(not facing_right)
        
        self.scene_textbox.set_visible(True)
        self.scene_textbox.queue_message(
            message, end_callback=lambda: [self.scene_textbox.set_visible(False), callback()]
        )

    def do_handle_event(self, event):
        if self._action_container.is_active("next") and self.control:
            self.scene_textbox.next_message()
from .custom_scenes import CustomBaseScene
import batFramework as bf
import pygame


class DialogueScene(CustomBaseScene):
    def __init__(self) -> None:
        super().__init__("dialogue")
        self.set_clear_color((0,0,0,0))
        text_box_height = 40
        text_box_speed = 30
        self.scene_textbox = bf.TextBox("dialogue_textbox")
        self.scene_textbox.resize(160, text_box_height)
        self.scene_textbox.set_position(0, 144 - text_box_height)
        self.scene_textbox.set_visible(False)
        self.scene_textbox.set_speed(text_box_speed)

        self.dimmer = bf.Entity(self.hud_camera.rect.size,convert_alpha=True)

        self.character_sprite = bf.Image(None)
        self.character_sprite.set_visible(False)
        self.current_character = None
        self.current_emotion = "neutral"
        

        self.dimmer.surface.fill((0,0,0))
        self.dimmer.set_visible(False)
        self.add_hud_entity(self.dimmer,self.character_sprite,self.scene_textbox)
        self.add_action(bf.Action("next").add_key_control(pygame.K_SPACE,pygame.K_RETURN))
        self.skippable : bool = True # can I skip current dialogue ?


    def on_enter(self):
        super().on_enter()
        self.manager._scenes[self.scene_index+1].set_active(True)
        self.manager._scenes[self.scene_index+1].set_visible(True)
        self.set_visible(False)
    

    def fade_in(self,duration=300):
        self.set_visible(True)
        self.dimmer.set_visible(True)
        if self.current_character: 
            print("show character sprite")
            self.character_sprite.set_visible(True)
        bf.EasingAnimation(
            "dimmer_fade_in",
            bf.Easing.EASE_IN_OUT,
            duration=duration,
            update_callback= lambda x : self.update_fade_alpha(x,"in"),
            end_callback=lambda : self.end_fade_alpha("in")).start()

    def fade_out(self,duration=300):
        bf.EasingAnimation(
            "dimmer_fade_in",
            bf.Easing.EASE_IN_OUT,
            duration=duration,
            update_callback= lambda x : self.update_fade_alpha(x,"out"),
            end_callback=lambda :self.end_fade_alpha("out")).start()

    def update_fade_alpha(self,progression,state:str):
        if state == "in":
            self.character_sprite.surface.set_alpha(int(255*progression))
            self.dimmer.surface.set_alpha(int(140*progression))
        elif state == "out":
            self.dimmer.surface.set_alpha(140-int(140*progression))
            self.character_sprite.surface.set_alpha(255-int(255*progression))

    def end_fade_alpha(self,state:str):
        if state=="in":
            self.character_sprite.surface.set_alpha(255)
            self.dimmer.surface.set_alpha(140)
        elif state == "out":
            self.dimmer.surface.set_alpha(0)
            self.dimmer.set_visible(False)
            self.character_sprite.set_visible(False)
            self.set_visible(False)


    def on_exit(self):
        self.character_sprite.set_visible(False)
        self.dimmer.set_visible(False)
        return super().on_exit()

    def set_visible(self, value: bool):
        return super().set_visible(value)

    def show_textbox(self):
        self.scene_textbox.set_visible(True)

    def hide_textbox(self):
        self.scene_textbox.set_visible(False)

    def next_message(self):
        self.scene_textbox.next_message()

    def say(
        self, message, character="", emotion="", facing_right=None, callback=None
    ):
        self.set_character(character,emotion,facing_right)
        self.scene_textbox.set_visible(True)
        self.scene_textbox.queue_message(
            message, end_callback=lambda: [self.scene_textbox.set_visible(False), callback()]
        )

    def do_handle_event(self, event):
        if self._action_container.is_active("next") and self.control:
            if self.scene_textbox.is_busy():
                self.scene_textbox.skip()
            else:
                self.scene_textbox.next_message()

    # empty string == keep current
    def set_character(self,character:str="",emotion:str="",facing_right:bool=None):
        # self.manager.print_status()
        print(f"set character {character} {emotion} {facing_right}")
        if facing_right is not None: 
            self.character_sprite.set_flip(not facing_right)

        if character == "" and emotion == "": return

        if character != "":
            if emotion == "": emotion = "neutral"
            self.current_character = character
            if facing_right is None : self.character_sprite.set_flip(False)
            if character is None : 
                self.character_sprite.set_visible(False)
                return
        if emotion != "":
            if emotion is None : emotion = "neutral"
            self.current_emotion = emotion

        # character or emotion is different that current -> get new image file
        character_path = f"sprites/{self.current_character}/{self.current_emotion}.png"
        print(character_path)
        self.character_sprite.set_image(bf.utils.get_path(character_path),True)
        if self.is_visible() : self.character_sprite.set_visible(True)

import batFramework as bf
from utils import style
import pygame

class CharacterNotDefinedException(Exception):
    "Character not defined previously"
    pass

def custom_set_visible(self:bf.Image,value:bool,dimmer:bf.Entity):
    # print("set visible")
    dimmer.set_visible(value)
    return bf.Image.set_visible(self,value)

def fade_in(self: bf.Image,duration=300):
    # print("fade in")
    # if self.visible : return
    self.surface.set_alpha(0)
    self.set_visible(True)
    bf.EasingAnimation(
        "sprite_image",
        bf.Easing.EASE_IN_OUT,
        duration,
        update_callback= lambda x : self.set_alpha(int(255*x))
    ).start()

def set_alpha(self: bf.Image,alpha,dimmer):
    self.surface.set_alpha(alpha)
    # print(alpha,int(alpha * 140/255))
    dimmer.surface.set_alpha(int(alpha * 140/255))

def fade_out(self: bf.Image,duration=300):
    # print("fade out")
    if not self.visible:return
    self.surface.set_alpha(255)
    bf.EasingAnimation(
        "sprite_image",
        bf.Easing.EASE_IN_OUT,
        duration,
        update_callback= lambda x : self.set_alpha(255-int(255*x)),
        end_callback=lambda:self.set_visible(False)
    ).start()

class CustomBaseScene(bf.Scene):
    def __init__(self, name, enable_alpha=True) -> None:
        super().__init__(name, enable_alpha)
        self.set_clear_color(bf.color.DARK_GB)
        self.control = True
        self._cutscene_action_container = bf.ActionContainer()

        text_box_height = 40
        self.scene_textbox = bf.TextBox(name+"_textbox")
        self.scene_textbox.resize(160, text_box_height)
        self.scene_textbox.set_position(0, 144 - text_box_height)
        self.scene_textbox.set_visible(False)

        self.background = bf.Image()

        self.character_sprite = bf.Image()
        
        self.current_character = None
        self.current_emotion = None

        self._cutscene_action_container.add_action(
            bf.Action("next").add_key_control(pygame.K_SPACE, pygame.K_RETURN)
        )

        self.dimmer = bf.Entity(self.hud_camera.rect.size,convert_alpha=True)
        self.dimmer.set_visible(False)
        self.dimmer.surface.set_alpha(140)
        self.add_hud_entity(self.background,self.dimmer, self.character_sprite, self.scene_textbox)

        self.character_sprite.set_visible = lambda val: custom_set_visible(self.character_sprite,val,self.dimmer) 
        self.character_sprite.fade_in = lambda  : fade_in(self.character_sprite)
        self.character_sprite.fade_out = lambda  : fade_out(self.character_sprite)
        self.character_sprite.set_alpha = lambda alpha,dimmer=self.dimmer : set_alpha(self.character_sprite,alpha,dimmer)

    def do_when_added(self):
        self.update(0.1)

    def add_hud_entity(self, *entity):
        super().add_hud_entity(*entity)
        for e in entity:
            style.stylize(e)

    # propagates event to all entities
    def process_event(self, event: pygame.Event):
        """
        Propagates event to child events. Calls early process event first, if returns False then stops. Processes scene's action_container, then custom do_handle_event function.
        Finally resets the action_container, and propagates to all child entities. if any of them returns True, the propagation is stopped.
        """
        if self.get_sharedVar("in_transition"):
            return
        if self.do_early_process_event(event):
            return
        
        if self.manager.get_sharedVar("in_cutscene"): 
            self._cutscene_action_container.process_event(event)
        else:
            self._action_container.process_event(event)

        ###### CUSTOM handle event for the textbox
        if self.control and self._cutscene_action_container.is_active("next"):
            self.next_message()
        #####
        self.do_handle_event(event)
        self._action_container.reset()
        self._cutscene_action_container.reset()
        if self.manager.get_sharedVar("in_cutscene") or not self.control: return
        for entity in self._world_entities + self._hud_entities:
            if entity.process_event(event):
                return



    #VN STUFF

    def on_exit(self):
        if self.current_character : self.set_sprite()
        if self.background.visible : self.set_background(None)


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
        self.scene_textbox.set_visible(True)

    def hide_textbox(self):
        self.scene_textbox.set_visible(False)

    def next_message(self):
        self.scene_textbox.next_message()

    def say(
        self, message, character=None, emotion=None, facing_right=None, callback=None
    ):
        if character is not None or emotion is not None:
            match (character, emotion):
                case (None, e) if e is not None:
                    self.set_emotion(e)
                    if facing_right is not None:
                        self.character_sprite.set_flip(not facing_right)
                case (_, _):
                    self.set_sprite(character, emotion,facing_right)
        else:
            if facing_right is not None:
                self.character_sprite.set_flip(not facing_right)
        
        # print(message)
        self.scene_textbox.set_visible(True)
        self.scene_textbox.queue_message(
            message, end_callback=lambda: [self.scene_textbox.set_visible(False), callback()]
        )



    def set_sprite(self, character=None, emotion=None, facing_right=None):
        print("set_sprite",self._name,character,emotion,facing_right)
        if not emotion:
            emotion = "neutral"
        if character is None:
            self.current_character = None
            self.character_sprite.fade_out()
            # self.character_sprite.set_visible(False)
            return
        character_change = self.current_character != character
        if character_change : self.character_sprite.set_flip(False)
        self.current_character = character
        self.current_emotion = emotion
        self.character_sprite.set_image(f"sprites/{character}/{emotion}.png", True)
        if facing_right is not None : self.character_sprite.set_flip(not facing_right)
        # self.character_sprite.set_visible(True)
        if character_change: 
            self.character_sprite.fade_in()
        else:
            self.character_sprite.set_visible(True)
    def set_emotion(self, emotion=None):
        # print("set_emotion",self.current_character,emotion)

        if self.current_character is None:
            raise CharacterNotDefinedException
        else:
            if not emotion:
                emotion = "neutral"

            self.character_sprite.set_image(
                f"sprites/{self.current_character}/{emotion}.png", True
            )
        self.current_emotion = emotion
        # self.character_sprite.set_visible(True)
        self.character_sprite.fade_in()


import pygame

from batFramework import Color
from batFramework.anchor import Anchor
from batFramework.button import Button
from batFramework.gui_container import GuiContainer
from batFramework.label import Label


class TreeContainer(GuiContainer):
    def __init__(
        self, title:str="MENU", root:bool=False) -> None:
        super().__init__()
        self._subs : dict[Button,"TreeContainer"] = {}
        self.set_color(Color.GRAY)
        self.set_layout("fit")
        self.set_alignement(Anchor.LEFT)
        self.set_anchor(Anchor.TOPLEFT)
        self.set_padding(10, 10)
        self.set_gap(10)
        self.set_show_focus(True)
        #self.set_focus_border_radius(10)
        self.set_focus_padding(10, 5)
        self.title = title
        self.titleLabel = Label(title)
        self.titleLabel.set_text_color(Color.BLACK)
        self.titleLabel.set_background_color(Color.WHITE)
        self.add(self.titleLabel)
        self.backButton = None
        self._is_root = root

        if not root:
            self.set_visible(False)

    def set_hud(self, value: bool):
        super().set_hud(value)
        for sub in self._subs:
            sub.set_hud(value)
    def switch_container(self, new: "GuiContainer", show=False):
        if not show:
            for sub  in self._subs.values():
                sub.switch_container(self,False)
        super().switch_container(new, show)

    def set_position(self, x, y):
        super().set_position(x, y)
        for button,sub in self._subs.items():
            sub.set_position(self.rect.right,button.rect.top)

    def set_scene_link(self, sceneLink):
        super().set_scene_link(sceneLink)
        for sub in self._subs.values():
            sceneLink.add_entity(sub)
    def set_visible(self, val: bool):
        super().set_visible(val)
        if not val:
            self.set_focus_index(0)

    def get_focus(self):
        print(self.title,"got focus")
        for sub  in self._subs.values():
            sub.lose_focus()
            sub.set_visible(False)
        super().get_focus()

    def lose_focus(self):
        for sub  in self._subs.values():
            sub.lose_focus()  
        super().lose_focus()
            
    def is_root(self):
        return self._is_root

    def set_title(self, name: str):
        if name != self.title:
            self.titleLabel.set_text(self.title)

    def get_title(self):
        return self.title

    def add_back_button(self, caller: GuiContainer, show=False):
        if self.backButton == None:
            self.backButton = Button("Back")
            self.backButton.set_id("BACK_BUTTON")
        self.backButton.set_callback(self.switch_container, caller, show)
        self.add_interactive(self.backButton)

    # No need to call add_entity on the scene, done automatically
    def add_container(self, other: "TreeContainer"):

        if self.get_scene_link() : self.get_scene_link().add_entity(other)
        other.add_back_button(self)
        other.set_hud(self.is_hud())
        link = Button(other.get_title())
        link.set_callback(self.switch_container, other, True)
        self.add_interactive(link)
        other.set_position(self.rect.right, link.rect.top)
        self._subs[link] = other

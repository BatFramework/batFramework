from ..utils import Singleton
from .widget import Widget

class Style:
    def __init__(self):
        pass

    def apply(self,widget:Widget):
        pass

class StyleManager(metaclass=Singleton):
    def __init__(self):
        self.styles :list[Style]= []
        self.widgets :set[Widget] = set()

    def register_widget(self,widget:Widget):
        self.widgets.add(widget)
        self.update()

    def remove_widget(self,widget: Widget):
        try:
            self.widgets.remove(widget)
        except KeyError:
            return
        self.update()

    def add(self,style:Style):
        self.styles.append(style)
        self.update()
    
    def update(self):
        for widget in self.widgets:
            for style in self.styles:
                style.apply(widget)
    

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
        self.lookup : dict[Widget,bool] = {}
        
    def register_widget(self,widget:Widget):
        self.widgets.add(widget)
        self.lookup[widget] = False
        self.update()

    def remove_widget(self,widget: Widget):
        try:
            self.widgets.remove(widget)
            self.lookup.pop(widget)
        except KeyError:
            return

    def add(self,style:Style):
        self.styles.append(style)
        self.lookup = {key: False for key in self.lookup}
        self.update()
    
    def update(self):
        for widget in self.widgets:
            if self.lookup[widget]: continue
            for style in self.styles:
                style.apply(widget)
            self.lookup[widget] = True

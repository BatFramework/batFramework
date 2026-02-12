from ..utils import Singleton
from .widget import Widget
from .style import Style,DefaultStyle
import batFramework as bf

class StyleManager(metaclass=Singleton):
    def __init__(self):
        self.styles: list[Style] = []
        self.widgets: set[Widget] = set()
        self.lookup: dict[Widget, bool] = {}
        self.add(DefaultStyle())

    def register_widget(self, widget: Widget):
        if widget in self.widgets:
            return
        self.widgets.add(widget)
        self.lookup[widget] = False
        self.update()

    def refresh_widget(self, widget: Widget):
        if widget in self.widgets:
            self.lookup[widget] = False
            self.update()

    def remove_widget(self, widget: Widget):
        if widget not in self.widgets:
            return
        self.widgets.remove(widget)
        self.lookup.pop(widget)

    def add(self, style: Style):
        self.styles.append(style)
        self.lookup = {key: False for key in self.lookup}
        self.update()

    def update_forced(self):
        for style in self.styles:
            for widget in self.widgets:    
                style.apply(widget)
        for key in self.lookup.keys():
            self.lookup[key] = True

    def update(self):
        for style in self.styles:
            for widget in self.widgets:
                if self.lookup[widget]:
                    continue
                style.apply(widget)
        for key in self.lookup.keys():
            self.lookup[key] = True

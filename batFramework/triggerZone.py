import batFramework as bf


class TriggerZone(bf.Entity):
    def __init__(self, size, trigger, callback, active=True) -> None:
        super().__init__(size, True)
        self.set_debug_color(bf.color.RIVER_BLUE)
        self.active = active
        self.callback = callback
        self.trigger = trigger

    def set_trigger(self, trigger):
        self.trigger = trigger
        return self

    def set_callback(self, callback):
        self.callback = callback
        return self

    def update(self, dt):
        if self.active and self.trigger():
            self.callback()

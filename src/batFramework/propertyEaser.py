from .easingController import EasingController
import pygame
from typing import Callable, Any, Self
import batFramework as bf


class PropertyEaser(EasingController):
    class EasedProperty:
        def __init__(
            self,
            getter: Callable[[], Any],
            setter: Callable[[Any], None],
            end_value: Any,
            start_value: Any = None,
        ):
            self.getter = getter
            self.setter = setter
            self.start_value = start_value if start_value is not None else getter()
            self.end_value = end_value

        def refresh_start_value(self):
            """Recapture the start value from the getter"""
            self.start_value = self.getter()

        def interpolate(self, t: float):
            a, b = self.start_value, self.end_value
            if type(a) != type(b):
                raise TypeError(f"start and end value should have the same type. {type(a)} and {type(b)} are not compatible.")
            if isinstance(a,(tuple,list)):
                try :
                    a = pygame.Vector2(*a)
                    b = pygame.Vector2(*b)
                except TypeError:
                    raise TypeError(f"Unsupported type for interpolation: {type(a)}")
            if isinstance(a, (int, float)):
                return a + (b - a) * t
            elif isinstance(a, pygame.Vector2):
                return a + (b - a) * t
            elif isinstance(a, pygame.Color):
                return pygame.Color(
                    round(a.r + (b.r - a.r) * t),
                    round(a.g + (b.g - a.g) * t),
                    round(a.b + (b.b - a.b) * t),
                    round(a.a + (b.a - a.a) * t),
                )
            else:
                raise TypeError(f"Unsupported type for interpolation: {type(a)}")

        def apply(self, t: float):
            self.setter(self.interpolate(t))

    def __init__(
        self,
        duration: float = 1,
        easing: bf.easing = bf.easing.LINEAR,
        loop: int = 0,
        register: str = "global",
        end_callback: Callable[[], Any] = None,
    ):
        self.properties: list[PropertyEaser.EasedProperty] = []

        def update_all(progress):
            for prop in self.properties:
                prop.apply(progress)

        super().__init__(duration, easing, update_all, end_callback, loop, register)

    def __str__(self):
        return f"(PROP){super().__str__()}"

    def start(self, force: bool = False):
        """Override start to refresh start values before starting the animation"""
        # Refresh all start values to current values
        for prop in self.properties:
            prop.refresh_start_value()
        return super().start(force)

    def add_attr(
        self,
        obj: Any,
        attr: str,
        end_value: Any,
        start_value: Any = None,
    ) -> Self:
        if start_value is not None:
            if type(start_value) != type(end_value):
                raise TypeError("start and end value should have the same type")
        self.properties.append(
            PropertyEaser.EasedProperty(
                getter=lambda o=obj, a=attr: getattr(o, a),
                setter=lambda v, o=obj, a=attr: setattr(o, a, v),
                end_value=end_value,
                start_value=start_value,
            )
        )
        return self

    def add_custom(
        self,
        getter: Callable[[], Any],
        setter: Callable[[Any], None],
        end_value: Any,
        start_value: Any = None,
    ) -> Self:
        self.properties.append(
            PropertyEaser.EasedProperty(getter, setter, end_value, start_value)
        )
        return self

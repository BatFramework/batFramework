from enum import IntEnum


class GuiLayer(IntEnum):
    NORMAL  = 0
    OVERLAY = 1   # dropdowns, context menus, transient popups
    MODAL   = 2   # blocking dialogs
    TOOLTIP = 3
    DEBUG   = 4
    
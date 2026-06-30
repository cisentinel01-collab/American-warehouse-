from PySide6.QtCore import QObject, Signal

class GlobalSignalManager(QObject):
    # Signals for data changes
    item_changed = Signal()
    supplier_changed = Signal()
    movement_added = Signal()
    location_changed = Signal()
    category_changed = Signal()
    user_changed = Signal()

signal_manager = GlobalSignalManager()

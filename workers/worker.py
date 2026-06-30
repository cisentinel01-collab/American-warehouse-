from PySide6.QtCore import QRunnable, Slot, QObject, Signal
import traceback, sys
from database.session import Session
from app_logging.app_logger import app_logger

class WorkerSignals(QObject):
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(int)

class Worker(QRunnable):
    """
    Worker thread for background tasks.
    Ensures that each thread manages its own DB session lifecycle.
    """
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        try:
            # Fn can access its thread-local session via database.session.Session
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            app_logger.error(f"Worker execution error: {e}\n{traceback.format_exc()}")
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
            try:
                Session.rollback()
            except: pass
        else:
            self.signals.result.emit(result)
        finally:
            # Crucial: remove the thread-local session to prevent leaks
            Session.remove()
            self.signals.finished.emit()

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QEasingCurve, QPoint
import qtawesome as qta

class Notification(QWidget):
    def __init__(self, message, icon="fa5s.info-circle", color="#1a2a6c", parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.frame = QWidget()
        self.frame.setObjectName("NotificationFrame")
        self.frame.setStyleSheet(f"""
            #NotificationFrame {{
                background-color: #ffffff;
                border: 2px solid {color};
                border-radius: 12px;
            }}
            QLabel {{
                color: {color};
                font-weight: bold;
                font-size: 14px;
            }}
        """)

        # Shadow effect for "Pro" look
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(Qt.black)
        shadow.setOffset(0, 5)
        self.frame.setGraphicsEffect(shadow)

        frame_layout = QHBoxLayout(self.frame)
        frame_layout.setContentsMargins(15, 15, 15, 15)
        frame_layout.setSpacing(10)

        icon_label = QLabel()
        icon_label.setPixmap(qta.icon(icon, color=color).pixmap(28, 28))
        frame_layout.addWidget(icon_label)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        frame_layout.addWidget(msg_label)

        self.layout.addWidget(self.frame)

        self.adjustSize()

        # Animation setup
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(600)
        self.anim.setEasingCurve(QEasingCurve.OutBack)

        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_notification)

    def show_notification(self, duration=4000):
        parent = self.parentWidget()
        if parent:
            start_x = parent.width() - self.width() - 30
            self.start_pos = QPoint(start_x, -self.height())
            self.end_pos = QPoint(start_x, 30)
        else:
            self.start_pos = QPoint(30, -self.height())
            self.end_pos = QPoint(30, 30)

        self.move(self.start_pos)
        self.show()

        self.anim.setStartValue(self.start_pos)
        self.anim.setEndValue(self.end_pos)
        self.anim.start()
        self.timer.start(duration)

    def hide_notification(self):
        self.anim.setDirection(QPropertyAnimation.Backward)
        self.anim.finished.connect(self.close)
        self.anim.start()

class NotificationManager:
    @staticmethod
    def success(parent, message):
        n = Notification(message, "fa5s.check-circle", "#27ae60", parent)
        n.show_notification()

    @staticmethod
    def error(parent, message):
        n = Notification(message, "fa5s.times-circle", "#e74c3c", parent)
        n.show_notification()

    @staticmethod
    def info(parent, message):
        n = Notification(message, "fa5s.info-circle", "#1a2a6c", parent)
        n.show_notification()

    @staticmethod
    def warning(parent, title, message):
        # Allow multi-param signature for consistency with Dashboard usage
        full_msg = f"{title}: {message}" if title else message
        n = Notification(full_msg, "fa5s.exclamation-triangle", "#f39c12", parent)
        n.show_notification()

import os
from PyQt6.QtWidgets import QSplashScreen, QLabel, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush

from spider_ide.ui.style_kit import DARK_THEME, mono


class BrutalistSpinner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(50)

    def rotate(self):
        self.angle = (self.angle + 45) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)
        pen = QPen(QColor(DARK_THEME['accent']), 2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(-8, -8, 16, 16)


class SplashScreen(QSplashScreen):
    def __init__(self):
        width, height = 600, 400
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(DARK_THEME['bg']))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        
        painter.setPen(QPen(QColor(DARK_THEME['grid']), 1))
        for x in range(0, width, 40):
            painter.drawLine(x, 0, x, height)
        for y in range(0, height, 40):
            painter.drawLine(0, y, width, y)
            
        painter.setPen(QPen(QColor(DARK_THEME['border']), 1))
        painter.drawRect(0, 0, width - 1, height - 1)
        painter.end()
        
        super().__init__(pixmap)
        
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        logo_label = QLabel("// SPIDER.IDE")
        logo_label.setFont(mono(14, bold=True, spacing=2))
        logo_label.setStyleSheet(f"color: {DARK_THEME['text']}; background: transparent;")
        top_layout.addWidget(logo_label)
        top_layout.addStretch()
        
        main_layout.addLayout(top_layout)
        main_layout.addStretch()
        
        center_layout = QVBoxLayout()
        center_layout.setSpacing(16)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel("INITIALIZING\nDEVELOPMENT ENVIRONMENT")
        title_label.setFont(mono(24, bold=True, spacing=4))
        title_label.setStyleSheet(f"color: {DARK_THEME['text']}; background: transparent;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(title_label)
        
        main_layout.addLayout(center_layout)
        main_layout.addStretch()
        
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        version_label = QLabel("VERSION 1.3.0")
        version_label.setFont(mono(10, spacing=1))
        version_label.setStyleSheet(f"color: {DARK_THEME['text_secondary']}; background: transparent;")
        bottom_layout.addWidget(version_label)
        bottom_layout.addStretch()
        
        loading_layout = QHBoxLayout()
        loading_layout.setSpacing(12)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        loading_label = QLabel("LOADING MODULES")
        loading_label.setFont(mono(10, bold=True, spacing=1))
        loading_label.setStyleSheet(f"color: {DARK_THEME['text_secondary']}; background: transparent;")
        loading_layout.addWidget(loading_label)
        
        self.spinner = BrutalistSpinner(self)
        loading_layout.addWidget(self.spinner)
        
        bottom_layout.addLayout(loading_layout)
        main_layout.addLayout(bottom_layout)
        
        self.setWindowOpacity(0.0)

    def show_animated(self, duration=5000):
        self.show()
        fade_in = QPropertyAnimation(self, b"windowOpacity")
        fade_in.setDuration(300)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        fade_in.start()
        self._fade_in = fade_in
        QTimer.singleShot(duration, self.close_splash)
        
    def close_splash(self):
        self.spinner.timer.stop()
        fade_out = QPropertyAnimation(self, b"windowOpacity")
        fade_out.setDuration(200)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        fade_out.finished.connect(self.close)
        fade_out.start()
        self._fade_out = fade_out 
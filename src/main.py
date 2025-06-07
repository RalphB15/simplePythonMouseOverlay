import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QSystemTrayIcon, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QSpinBox, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QPainter, QIcon, QCursor, QColor
import win32gui  # type: ignore
import win32con  # type: ignore

class OverlayWindow(QWidget):
    def __init__(self, size=13, thickness=2, gap=6):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Crosshair-Configuration
        self.crosshair_size = size
        self.crosshair_thickness = thickness
        self.crosshair_gap = gap
        self.crosshair_color = QColor(Qt.GlobalColor.green)
        self.crosshair_border_color = QColor(Qt.GlobalColor.black)
        self.crosshair_border_width = 1
        self.refresh_rate = 10  # in milliseconds

        screen_rect = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_rect)
        self.hwnd = self.winId().__int__()
        self.make_click_through()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(self.refresh_rate) # Update every 10 ms 10 = 100 FPS

    def make_click_through(self):
        ex_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        ex_style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, ex_style)

    def drawRectWithBorder(self, painter, rect):
        painter.setBrush(self.crosshair_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(rect)
        if self.crosshair_border_width > 0:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(self.crosshair_border_color)
            painter.drawRect(rect)

    def paintEvent(self, _event):
        painter = QPainter(self)
        mouse_pos = QCursor.pos()
        size = self.crosshair_size
        thickness = self.crosshair_thickness
        gap = self.crosshair_gap
        x, y = mouse_pos.x(), mouse_pos.y()

        # Horizontale Line
        left_end = x - gap // 2
        right_start = x + (gap + 1) // 2
        left_width = left_end - (x - size)
        right_width = (x + size) - right_start

        left_rect = QRect(x - size, y - thickness // 2, left_width, thickness)
        right_rect = QRect(right_start, y - thickness // 2, right_width, thickness)
        self.drawRectWithBorder(painter, left_rect)
        self.drawRectWithBorder(painter, right_rect)

        # Vertikale Line
        top_end = y - gap // 2
        bottom_start = y + (gap + 1) // 2
        top_height = top_end - (y - size)
        bottom_height = (y + size) - bottom_start

        top_rect = QRect(x - thickness // 2, y - size, thickness, top_height)
        bottom_rect = QRect(x - thickness // 2, bottom_start, thickness, bottom_height)
        self.drawRectWithBorder(painter, top_rect)
        self.drawRectWithBorder(painter, bottom_rect)

class ConfigWindow(QWidget):
    def __init__(self, overlay: OverlayWindow):
        super().__init__()
        self.overlay = overlay
        self.setWindowTitle("Configure Crosshair")
        self.setGeometry(100, 100, 300, 300)

        layout = QVBoxLayout()

        group = QGroupBox("Crosshair Parameter")
        group_layout = QVBoxLayout()

        # Refreshrate parameter
        refresh_layout = QHBoxLayout()
        refresh_label = QLabel("Refreshrate (ms):")
        self.refresh_spin = QSpinBox()
        self.refresh_spin.setRange(1, 1000)
        self.refresh_spin.setValue(self.overlay.refresh_rate)
        self.refresh_spin.valueChanged.connect(self.update_refresh_rate)
        refresh_layout.addWidget(refresh_label)
        refresh_layout.addWidget(self.refresh_spin)
        group_layout.addLayout(refresh_layout)

        # Size parameter
        size_layout = QHBoxLayout()
        size_label = QLabel("Size:")
        self.size_spin = QSpinBox()
        self.size_spin.setRange(5, 100)
        self.size_spin.setValue(self.overlay.crosshair_size)
        self.size_spin.valueChanged.connect(self.update_overlay)
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_spin)
        group_layout.addLayout(size_layout)

        # Thickness parameter
        thickness_layout = QHBoxLayout()
        thickness_label = QLabel("Thickness:")
        self.thickness_spin = QSpinBox()
        self.thickness_spin.setRange(1, 20)
        self.thickness_spin.setValue(self.overlay.crosshair_thickness)
        self.thickness_spin.valueChanged.connect(self.update_overlay)
        thickness_layout.addWidget(thickness_label)
        thickness_layout.addWidget(self.thickness_spin)
        group_layout.addLayout(thickness_layout)

        # Gap parameter
        gap_layout = QHBoxLayout()
        gap_label = QLabel("Gap:")
        self.gap_spin = QSpinBox()
        self.gap_spin.setRange(0, 50)
        self.gap_spin.setValue(self.overlay.crosshair_gap)
        self.gap_spin.valueChanged.connect(self.update_overlay)
        gap_layout.addWidget(gap_label)
        gap_layout.addWidget(self.gap_spin)
        group_layout.addLayout(gap_layout)

        # Fill Color parameter
        color_layout = QHBoxLayout()
        color_label = QLabel("Fill color:")
        self.color_button = QPushButton("Select")
        self.color_button.clicked.connect(self.choose_color)
        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_button)
        group_layout.addLayout(color_layout)

        # Border Color parameter
        border_layout = QHBoxLayout()
        border_label = QLabel("Border color:")
        self.border_button = QPushButton("Select")
        self.border_button.clicked.connect(self.choose_border_color)
        border_layout.addWidget(border_label)
        border_layout.addWidget(self.border_button)
        group_layout.addLayout(border_layout)

        # Border Thickness parameter
        bt_layout = QHBoxLayout()
        bt_label = QLabel("Border Dicke:")
        self.bt_spin = QSpinBox()
        self.bt_spin.setRange(0, 10)
        self.bt_spin.setValue(self.overlay.crosshair_border_width)
        self.bt_spin.valueChanged.connect(self.update_overlay)
        bt_layout.addWidget(bt_label)
        bt_layout.addWidget(self.bt_spin)
        group_layout.addLayout(bt_layout)

        group.setLayout(group_layout)
        layout.addWidget(group)
        self.setLayout(layout)

    def update_refresh_rate(self):
        new_rate = self.refresh_spin.value()
        if new_rate > 0:
            self.overlay.refresh_rate = new_rate
            self.overlay.timer.start(new_rate)
        else:
            self.overlay.timer.stop()

    def update_overlay(self):
        self.overlay.crosshair_size = self.size_spin.value()
        self.overlay.crosshair_thickness = self.thickness_spin.value()
        self.overlay.crosshair_gap = self.gap_spin.value()
        self.overlay.crosshair_border_width = self.bt_spin.value()
        self.overlay.update()

    def choose_color(self):
        from PyQt6.QtWidgets import QColorDialog
        color = QColorDialog.getColor(initial=self.overlay.crosshair_color, parent=self)
        if color.isValid():
            self.overlay.crosshair_color = color
            self.overlay.update()

    def choose_border_color(self):
        from PyQt6.QtWidgets import QColorDialog
        color = QColorDialog.getColor(initial=self.overlay.crosshair_border_color, parent=self)
        if color.isValid():
            self.overlay.crosshair_border_color = color
            self.overlay.update()

def show_system_cursor():
    QApplication.restoreOverrideCursor()

if __name__ == "__main__":
    from PyQt6.QtGui import QGuiApplication
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)

    QApplication.setOverrideCursor(QCursor(Qt.CursorShape.BlankCursor))

    overlay = OverlayWindow()
    overlay.show()

    config = ConfigWindow(overlay)
    config.show()

    #tray_icon = QSystemTrayIcon(QIcon("mouse.png"), app)
    #tray_icon.setToolTip("Mouse Overlay")
    #tray_icon.show()

    try:
        sys.exit(app.exec())
    finally:
        show_system_cursor()
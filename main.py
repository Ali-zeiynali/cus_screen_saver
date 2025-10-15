import sys, os, itertools, datetime
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QWidget,
    QGraphicsOpacityEffect,
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QEvent
from PyQt5.QtGui import QPixmap, QFont, QCursor, QFontDatabase

IMAGE_FOLDER = "images"       # پوشه تصاویر
SLIDE_DELAY_MS = 5000         # میلی‌ثانیه
FADE_DURATION_MS = 800        # مدت زمان افکت فید
DAY_FONT_PATH = os.path.join("fonts", "Anurati-Regular.otf")

class ScreenSaver(QWidget):
    def __init__(self):
        super().__init__()

        # وضعیت اولیه
        self.current_path = None
        self.images = []
        self.image_iter = None
        self.scaled_cache = {}

        # فول‌اسکرین و موس مخفی
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setCursor(QCursor(Qt.BlankCursor))
        self.setStyleSheet("background-color: black;")
        self.showFullScreen()
        self.setMouseTracking(True)
        self.installEventFilter(self)

        # لیبل تصویر
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMouseTracking(True)
        self.opacity_effect = QGraphicsOpacityEffect(self.image_label)
        self.image_label.setGraphicsEffect(self.opacity_effect)
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity", self)
        self.fade_animation.setDuration(FADE_DURATION_MS)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)

        # لیبل روز
        self.day_label = QLabel(self)
        self.day_label.setStyleSheet(
            "color: rgba(255, 255, 255, 204); background: transparent; letter-spacing: 2px;"
        )
        self.day_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)

        # لیبل ساعت
        self.time_label = QLabel(self)
        self.time_label.setStyleSheet("color: white; background: transparent;")
        self.time_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.time_label.setMouseTracking(True)

        self.day_font_family = self.load_custom_font(DAY_FONT_PATH, "Anurati")

        # بارگذاری تصاویر
        if os.path.isdir(IMAGE_FOLDER):
            self.images = [os.path.join(IMAGE_FOLDER, f)
                           for f in sorted(os.listdir(IMAGE_FOLDER))
                           if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp"))]
        if self.images:
            self.image_iter = itertools.cycle(self.images)

        # تایمر عکس
        if self.image_iter:
            self.timer_img = QTimer(self)
            self.timer_img.timeout.connect(self.show_next_image)
            self.timer_img.start(SLIDE_DELAY_MS)

        # تایمر ساعت
        self.timer_clock = QTimer(self)
        self.timer_clock.timeout.connect(self.update_clock)
        self.timer_clock.start(1000)

        # نمایش اولیه
        self.show_next_image()
        self.update_clock()

    def show_next_image(self):
        if not self.image_iter:
            self.image_label.setText("No images in ./images")
            self.image_label.setStyleSheet("color: gray;")
            self.image_label.setAlignment(Qt.AlignCenter)
            return

        self.current_path = next(self.image_iter)
        self.update_pixmap()

    def update_pixmap(self, animate=True):
        if not self.current_path:
            return
        pm = QPixmap(self.current_path)
        if pm.isNull():
            return
        screen_rect = self.rect()
        if not screen_rect.width() or not screen_rect.height():
            return
        cache_key = (
            self.current_path,
            screen_rect.width(),
            screen_rect.height(),
        )
        if cache_key in self.scaled_cache:
            scaled = self.scaled_cache[cache_key]
        else:
            scaled = pm.scaled(
                screen_rect.width(),
                screen_rect.height(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation,
            )
            if len(self.scaled_cache) > 20:
                self.scaled_cache.clear()
            self.scaled_cache[cache_key] = scaled

        self.image_label.setPixmap(scaled)
        self.image_label.setGeometry(self.rect())
        if animate:
            self.play_fade_animation()
        else:
            self.opacity_effect.setOpacity(1.0)

    def play_fade_animation(self):
        if self.fade_animation.state() == QPropertyAnimation.Running:
            self.fade_animation.stop()
        self.opacity_effect.setOpacity(0.0)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()

    def update_clock(self):
        now = datetime.datetime.now()
        day_name = now.strftime("%A")   # روز به انگلیسی
        time_str = now.strftime("%H:%M")

        w, h = self.width(), self.height()
        day_font = QFont(self.day_font_family, max(int(h * 0.1), 24))
        day_font.setCapitalization(QFont.AllUppercase)
        self.day_label.setFont(day_font)

        self.time_label.setFont(QFont("Arial", max(int(h * 0.07), 18)))

        self.day_label.setText(day_name.upper())
        self.time_label.setText(time_str)

        # جایگذاری پایین صفحه
        self.day_label.setGeometry(0, int(h * 0.72), w, int(h * 0.14))
        self.time_label.setGeometry(0, int(h * 0.84), w, int(h * 0.12))

    def load_custom_font(self, font_path, fallback_family):
        if os.path.isfile(font_path):
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    return families[0]
        return fallback_family

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_pixmap(animate=False)
        self.update_clock()

    def eventFilter(self, obj, event):
        if event.type() in (
            QEvent.MouseMove,
            QEvent.MouseButtonPress,
            QEvent.MouseButtonDblClick,
            QEvent.Wheel,
            QEvent.HoverMove,
        ):
            self.close()
            return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        self.close()

    def mousePressEvent(self, event):
        self.close()

    def mouseMoveEvent(self, event):
        self.close()

    def mouseDoubleClickEvent(self, event):
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    saver = ScreenSaver()
    saver.show()
    sys.exit(app.exec_())

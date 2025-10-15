import sys, os, itertools, datetime
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QEasingCurve, QPropertyAnimation
from PyQt5.QtGui import QPixmap, QFont, QCursor

IMAGE_FOLDER   = "images"      # پوشه‌ی تصاویر کنار فایل
SLIDE_DELAY_MS = 5000          # زمان هر اسلاید (میلی‌ثانیه)

class ScreenSaver(QWidget):
    def __init__(self):
        super().__init__()

        # ---------- وضعیت اولیه و متغیرها ----------
        self.current_path = None
        self.target_path = None
        self.images = []
        self.image_iter = None
        self.pixmap_cache = {}

        # لیست تصاویر
        if os.path.isdir(IMAGE_FOLDER):
            self.images = [os.path.join(IMAGE_FOLDER, f)
                           for f in sorted(os.listdir(IMAGE_FOLDER))
                           if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp"))]
        if self.images:
            self.image_iter = itertools.cycle(self.images)

        # ---------- ویجت‌ها را بساز (قبل از showFullScreen) ----------
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setCursor(QCursor(Qt.BlankCursor))
        self.setStyleSheet("background-color: black;")

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMouseTracking(True)

        self.opacity_effect = QGraphicsOpacityEffect(self.image_label)
        self.image_label.setGraphicsEffect(self.opacity_effect)
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity", self)
        self.fade_anim.setDuration(800)
        self.fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_anim.finished.connect(self.on_fade_finished)
        self._fade_direction = None

        self.day_label = QLabel(self)
        self.day_label.setStyleSheet(
            "color: rgba(255, 255, 255, 0.8); background: transparent; letter-spacing: 2px;"
        )
        self.day_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.day_label.setMouseTracking(True)

        self.time_label = QLabel(self)
        self.time_label.setStyleSheet("color: white; background: transparent;")
        self.time_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self.time_label.setMouseTracking(True)

        self.setMouseTracking(True)

        # ---------- تایمرها ----------
        self.timer_img = QTimer(self)
        self.timer_img.timeout.connect(self.show_next_image)
        if self.image_iter:
            self.timer_img.start(SLIDE_DELAY_MS)

        self.timer_clock = QTimer(self)
        self.timer_clock.timeout.connect(self.update_clock)
        self.timer_clock.start(1000)

        # اولین نمایش قبل از فول‌اسکرین
        self.show_next_image()
        self.update_clock()

        # حالا فول‌اسکرین کن (بعد از ساخت همه‌ی ویجت‌ها)
        self.showFullScreen()

    # ---------- منطق نمایش ----------
    def show_next_image(self):
        if not self.image_iter:
            self.image_label.setText("No images in ./images")
            self.image_label.setStyleSheet("color: gray;")
            self.image_label.setAlignment(Qt.AlignCenter)
            return
        next_path = next(self.image_iter)
        if self.fade_anim.state() == QPropertyAnimation.Running:
            self.fade_anim.stop()
            self._fade_direction = None
            self.opacity_effect.setOpacity(1.0)

        self.target_path = next_path

        if self.current_path is None:
            self.current_path = next_path
            self.update_pixmap()
            self.start_fade(direction="in")
        else:
            self.start_fade(direction="out")

    def update_pixmap(self):
        if not self.current_path:
            return
        pm = self.pixmap_cache.get(self.current_path)
        if pm is None:
            pm = QPixmap(self.current_path)
            if pm.isNull():
                return
            self.pixmap_cache[self.current_path] = pm
        if pm.isNull():
            return
        r = self.rect()
        scaled = pm.scaled(r.width(), r.height(),
                           Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)
        self.image_label.setGeometry(self.rect())

    def start_fade(self, direction):
        if direction == "in":
            self._fade_direction = "in"
            self.opacity_effect.setOpacity(0.0)
            self.fade_anim.setStartValue(0.0)
            self.fade_anim.setEndValue(1.0)
            self.fade_anim.start()
        elif direction == "out":
            self._fade_direction = "out"
            self.opacity_effect.setOpacity(1.0)
            self.fade_anim.setStartValue(1.0)
            self.fade_anim.setEndValue(0.0)
            self.fade_anim.start()

    def on_fade_finished(self):
        if self._fade_direction == "out" and self.target_path:
            self.current_path = self.target_path
            self.update_pixmap()
            self.start_fade(direction="in")
        else:
            self._fade_direction = None
            self.target_path = None

    def update_clock(self):
        # اگر لیبل‌ها هنوز ساخته نشده‌اند، از خطا جلوگیری کن
        if not hasattr(self, "day_label") or not hasattr(self, "time_label"):
            return

        now = datetime.datetime.now()
        day_en   = now.strftime("%A").upper()   # اسم روز انگلیسی
        time_str = now.strftime("%H:%M")

        w, h = max(1, self.width()), max(1, self.height())
        day_fs  = max(28, int(h * 0.09))   # بزرگتر از قبل
        time_fs = max(18, int(h * 0.045))  # ~۴.۵٪ ارتفاع

        day_font = QFont("Anurati", day_fs)
        day_font.setLetterSpacing(QFont.AbsoluteSpacing, 1.5)
        self.day_label.setFont(day_font)
        self.time_label.setFont(QFont("Arial", time_fs))

        self.day_label.setText(day_en)
        self.time_label.setText(time_str)

        # جایگذاری پایین صفحه
        day_h  = int(day_fs * 1.4)
        time_h = int(time_fs * 1.4)
        gap = int(h * 0.012)
        bottom = int(h * 0.03)

        day_y  = h - bottom - day_h
        time_y = day_y - gap - time_h

        self.day_label.setGeometry(0, day_y,  w, day_h)
        self.time_label.setGeometry(0, time_y, w, time_h)

    # ---------- رویدادها ----------
    def resizeEvent(self, event):
        # گارد: ممکنه قبل از ساخت کامل ویجت‌ها صدا زده شود
        if hasattr(self, "image_label"):
            self.image_label.setGeometry(self.rect())
        self.update_pixmap()
        self.update_clock()
        super().resizeEvent(event)

    def keyPressEvent(self, event):
        self.close()

    def mouseMoveEvent(self, event):
        self.close()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    saver = ScreenSaver()
    saver.show()
    sys.exit(app.exec_())

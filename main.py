import sys, os, itertools, datetime
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont, QCursor

IMAGE_FOLDER   = "images"      # پوشه‌ی تصاویر کنار فایل
SLIDE_DELAY_MS = 5000          # زمان هر اسلاید (میلی‌ثانیه)

class ScreenSaver(QWidget):
    def __init__(self):
        super().__init__()

        # ---------- وضعیت اولیه و متغیرها ----------
        self.current_path = None
        self.images = []
        self.image_iter = None

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

        self.day_label = QLabel(self)
        self.day_label.setStyleSheet("color: white; background: transparent;")
        self.day_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)

        self.time_label = QLabel(self)
        self.time_label.setStyleSheet("color: white; background: transparent;")
        self.time_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)

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
        self.current_path = next(self.image_iter)
        self.update_pixmap()

    def update_pixmap(self):
        if not self.current_path:
            return
        pm = QPixmap(self.current_path)
        if pm.isNull():
            return
        r = self.rect()
        scaled = pm.scaled(r.width(), r.height(),
                           Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)
        self.image_label.setGeometry(self.rect())

    def update_clock(self):
        # اگر لیبل‌ها هنوز ساخته نشده‌اند، از خطا جلوگیری کن
        if not hasattr(self, "day_label") or not hasattr(self, "time_label"):
            return

        now = datetime.datetime.now()
        day_en   = now.strftime("%A")   # اسم روز انگلیسی
        time_str = now.strftime("%H:%M")

        w, h = max(1, self.width()), max(1, self.height())
        day_fs  = max(24, int(h * 0.07))   # ~۷٪ ارتفاع
        time_fs = max(18, int(h * 0.045))  # ~۴.۵٪ ارتفاع

        self.day_label.setFont(QFont("Arial", day_fs, QFont.Bold))
        self.time_label.setFont(QFont("Arial", time_fs))

        self.day_label.setText(day_en)
        self.time_label.setText(time_str)

        # جایگذاری پایین صفحه
        day_h  = int(day_fs * 1.4)
        time_h = int(time_fs * 1.4)
        gap = int(h * 0.012)
        bottom = int(h * 0.05)

        time_y = h - bottom - time_h
        day_y  = time_y - gap - day_h

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
        if event.key() in (Qt.Key_Escape, Qt.Key_Q):
            self.close()

    def mousePressEvent(self, event):
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    saver = ScreenSaver()
    saver.show()
    sys.exit(app.exec_())

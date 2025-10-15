import sys, os, itertools, datetime
from PyQt5.QtWidgets import QApplication, QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont, QCursor

IMAGE_FOLDER = "images"       # پوشه تصاویر
SLIDE_DELAY_MS = 5000         # میلی‌ثانیه

class ScreenSaver(QWidget):
    def __init__(self):
        super().__init__()

        # وضعیت اولیه
        self.current_path = None
        self.images = []
        self.image_iter = None

        # فول‌اسکرین و موس مخفی
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setCursor(QCursor(Qt.BlankCursor))
        self.setStyleSheet("background-color: black;")
        self.showFullScreen()

        # لیبل تصویر
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)

        # لیبل روز
        self.day_label = QLabel(self)
        self.day_label.setStyleSheet("color: white; background: transparent;")
        self.day_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)

        # لیبل ساعت
        self.time_label = QLabel(self)
        self.time_label.setStyleSheet("color: white; background: transparent;")
        self.time_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)

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

    def update_pixmap(self):
        if not self.current_path:
            return
        pm = QPixmap(self.current_path)
        if pm.isNull():
            return
        screen_rect = self.rect()
        scaled = pm.scaled(screen_rect.width(), screen_rect.height(),
                           Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)
        self.image_label.setGeometry(self.rect())

    def update_clock(self):
        now = datetime.datetime.now()
        day_name = now.strftime("%A")   # روز به انگلیسی
        time_str = now.strftime("%H:%M")

        w, h = self.width(), self.height()
        self.day_label.setFont(QFont("Arial", int(h * 0.07), QFont.Bold))
        self.time_label.setFont(QFont("Arial", int(h * 0.05)))

        self.day_label.setText(day_name)
        self.time_label.setText(time_str)

        # جایگذاری پایین صفحه
        self.day_label.setGeometry(0, h - 150, w, 60)
        self.time_label.setGeometry(0, h - 80, w, 60)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_pixmap()
        self.update_clock()

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

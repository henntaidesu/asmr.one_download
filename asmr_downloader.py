from src.UI.download_page import DownloadPage
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QFont
from PyQt6.QtCore import Qt
import sys
import ctypes


# pyinstaller --noconsole --onefile main.py


def create_emoji_icon(emoji, size=64):
    """创建基于emoji的图标"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 设置字体
    font = QFont()
    font.setPixelSize(int(size * 0.8))
    painter.setFont(font)

    # 绘制emoji
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, emoji)
    painter.end()

    return QIcon(pixmap)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    app.setWindowIcon(create_emoji_icon("🎧"))

    window = DownloadPage()
    window.setWindowIcon(create_emoji_icon("🎧"))
    window.show()
    sys.exit(app.exec())

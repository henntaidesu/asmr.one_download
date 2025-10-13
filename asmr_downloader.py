from src.UI.download_page import DownloadPage
from src.UI.set_config import SetConfig
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QFont
from PyQt6.QtCore import Qt
import sys
import ctypes
import os

# pyinstaller --noconsole --onefile --icon=imge/hp.ico asmr_downloader.py

APP_VERSION = "v2.1.5"
APP_NAME = "ASMR_Downloader"
APP_FULL_TITLE = f"{APP_NAME}_{APP_VERSION}"
START_MODE = "download"
WINDOW_ICON = "🎧"



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


def start_download_page():
    """启动下载页面"""
    window = DownloadPage()
    window.setWindowIcon(create_emoji_icon(WINDOW_ICON))
    window.setWindowTitle(APP_FULL_TITLE)
    window.show()
    return window


def start_settings_page():
    """启动设置页面"""
    window = SetConfig()
    window.setWindowIcon(create_emoji_icon(WINDOW_ICON))
    window.setWindowTitle(f"{APP_FULL_TITLE} - 设置")
    window.show()
    return window


def main():
    """主程序入口 - 可配置的启动方式"""
    app = QApplication(sys.argv)
    
    # 设置应用图标
    app.setWindowIcon(create_emoji_icon(WINDOW_ICON))
    
    # 根据配置启动不同页面
    if START_MODE == "settings":
        print(f"启动 {APP_FULL_TITLE} - 设置页面")
        window = start_settings_page()
    else:  # 默认启动下载页面
        print(f"启动 {APP_FULL_TITLE} - 下载页面")
        window = start_download_page()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

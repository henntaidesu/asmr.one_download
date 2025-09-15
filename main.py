from src.UI.download_page import DownloadPage
from PyQt6.QtWidgets import QApplication
import sys
import ctypes

# PyInstaller打包命令：
# pyinstaller --noconsole --onefile main.py
# 或者使用spec文件: pyinstaller main.spec

if __name__ == '__main__':
    # 检查是否为exe运行，如果是则隐藏控制台窗口
    if getattr(sys, 'frozen', False):
        # 当打包为exe时隐藏控制台
        try:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass  # 忽略在非Windows系统上的错误

    app = QApplication(sys.argv)
    window = DownloadPage()
    window.show()
    sys.exit(app.exec())

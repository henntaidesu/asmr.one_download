from src.UI.download_page import DownloadPage
from PyQt6.QtWidgets import QApplication
import sys
import ctypes


# pyinstaller --noconsole --onefile main.py


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DownloadPage()
    window.show()
    sys.exit(app.exec())

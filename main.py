from src.UI.index import INDEX
from PyQt6.QtWidgets import QApplication
import sys
import ctypes

# pyinstaller --noconsole --onefile main.py

if __name__ == '__main__':
    # not_start_CLI
    # ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    app = QApplication(sys.argv)
    window = INDEX()
    window.show()
    sys.exit(app.exec())

from src.UI.index import INDEX
from PyQt6.QtWidgets import QApplication
import sys


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = INDEX()
    window.show()
    sys.exit(app.exec())

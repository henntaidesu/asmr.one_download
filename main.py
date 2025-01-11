from src.read_conf import ReadConf
from src.UI.index import INDEX
import sys
from PyQt6.QtWidgets import QApplication

app = QApplication(sys.argv)
window = INDEX()
window.show()
sys.exit(app.exec())


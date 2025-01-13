from src.read_conf import ReadConf
from src.UI.index import INDEX
import sys
from PyQt6.QtWidgets import QApplication
from src.asmr_api.get_down_list import get_down_list
import threading



class Index:

    def __init__(self):
        self.conf = ReadConf()


    def index(self):
        thread1 = threading.Thread(target=self.start_UI)
        thread1.start()

    @staticmethod
    def start_UI():
        # get_down_list()
        app = QApplication(sys.argv)
        window = INDEX()
        window.show()
        sys.exit(app.exec())


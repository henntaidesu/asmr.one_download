import os
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QMessageBox, QTextEdit
from PyQt6.uic import loadUi
from src.asmr_api.get_asmr_works import get_asmr_downlist_api
from src.read_conf import ReadConf
from src.UI.creat_ui_file import creat_ui_file


class DownloadThread(QThread):
    download_finished = pyqtSignal(str)
    download_progress = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._is_running = True  # 控制线程是否运行

    def run(self):
        try:
            get_asmr_downlist_api()  # 执行下载操作
            self.download_finished.emit("下载任务已完成！")
        except Exception as e:
            self.download_finished.emit(f"发生错误: {str(e)}")

    def stop(self):
        self._is_running = False  # 设置停止标志

    def is_running(self):
        return self._is_running


class INDEX(QMainWindow):
    def __init__(self):
        super().__init__()

        if not os.path.exists('src/UI/index.ui'):
            creat_ui_file()

        loadUi('src/UI/index.ui', self)  # 加载.ui文件

        # 连接信号到方法
        self.down_start_button = self.findChild(QPushButton, 'pushButton')
        self.down_start_button.clicked.connect(self.down_start)

        self.down_stop_button = self.findChild(QPushButton, 'pushButton_2')
        self.down_stop_button.clicked.connect(self.down_start)

        self.path_conf_save_button = self.findChild(QPushButton, 'path_conf_save')
        self.path_conf_save_button.clicked.connect(self.save_download_path)

        self.user_conf_save_button = self.findChild(QPushButton, 'user_conf_save')
        self.user_conf_save_button.clicked.connect(self.save_user)

        self.download_path_QLineEdit = self.findChild(QLineEdit, 'down_path')
        self.speed_limit_QLineEdit = self.findChild(QLineEdit, 'speed_limit')
        self.user_name_QlineEdit = self.findChild(QLineEdit, 'user_name')
        self.user_password_QlineEdit = self.findChild(QLineEdit, 'password')

        self.conf = ReadConf()
        self.set_data()

    def set_data(self):
        user_info = self.conf.read_asmr_user()
        download_path = self.conf.read_download_conf()
        speed_limit = str(download_path[0])
        self.user_name_QlineEdit.setText(user_info['username'])
        self.user_password_QlineEdit.setText(user_info['passwd'])
        self.speed_limit_QLineEdit.setText(speed_limit)
        self.download_path_QLineEdit.setText(download_path[1])

    def save_download_path(self):
        download_path = self.download_path_QLineEdit.text()
        speed_limit = self.speed_limit_QLineEdit.text()
        self.conf.write_download_conf(speed_limit, download_path)

    def save_user(self):
        from src.asmr_api.login import login
        user_name = self.user_name_QlineEdit.text()
        password = self.user_password_QlineEdit.text()
        self.conf.write_asmr_username(user_name, password)
        message = login()
        if message is not True:
            self.show_message_box(message, 'from asmr.one')

    def show_message_box(self, message, message_from):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(message)
        msg.setWindowTitle(message_from)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        msg.exec()

    def down_start(self):
        print('开始下载')
        self.download_thread = DownloadThread()
        self.download_thread.download_finished.connect(self.show_message_box)
        self.download_thread.start()  # 启动后台下载线程
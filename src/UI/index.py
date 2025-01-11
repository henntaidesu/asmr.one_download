import os
from distutils.command.config import config

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QMessageBox, QComboBox, QLabel
from PyQt6.uic import loadUi
from src.asmr_api.get_asmr_works import get_asmr_downlist_api
from src.read_conf import ReadConf
from PyQt6 import QtCore, QtWidgets


class DownloadThread(QThread):
    download_finished = pyqtSignal(str)
    download_progress = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._is_running = True  # 控制线程是否运行

    def run(self):
        try:
            get_asmr_downlist_api()  # 执行下载操作
        except Exception as e:
            self.download_finished.emit(f"发生错误: {str(e)}")

    def stop(self):
        self._is_running = False  # 设置停止标志

    def is_running(self):
        return self._is_running


class INDEX(QMainWindow):
    def __init__(self):
        super().__init__()

        # 创建界面组件
        self.setWindowTitle("ASMR_download")
        self.setGeometry(100, 100, 400, 200)

        self.centralwidget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.centralwidget)

        # 创建并配置 QLineEdit
        self.down_path = QLineEdit(self.centralwidget)
        self.down_path.setGeometry(QtCore.QRect(80, 10, 220, 30))
        self.down_path.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.down_path.setPlaceholderText("Download_PATH")

        self.user_name = QLineEdit(self.centralwidget)
        self.user_name.setGeometry(QtCore.QRect(10, 50, 140, 30))
        self.user_name.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.user_name.setPlaceholderText("user_name")

        self.password = QLineEdit(self.centralwidget)
        self.password.setGeometry(QtCore.QRect(160, 50, 140, 30))
        self.password.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.password.setPlaceholderText("password")

        self.speed_limit = QLineEdit(self.centralwidget)
        self.speed_limit.setGeometry(QtCore.QRect(10, 10, 60, 30))
        self.speed_limit.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.speed_limit.setPlaceholderText("speed")

        # 创建下拉选择框
        self.folder_name_type_combo_box = QComboBox(self.centralwidget)
        self.folder_name_type_combo_box.setGeometry(QtCore.QRect(120, 90, 100, 30))
        self.folder_name_type_combo_box.addItem("RJ号命名")  # 添加选项1
        self.folder_name_type_combo_box.addItem("标题命名")  # 添加选项2
        self.folder_name_type_combo_box.currentTextChanged.connect(self.on_combo_changed)

        # 文本
        self.label = QLabel("文件命名方式", self.centralwidget)
        self.label.setGeometry(QtCore.QRect(10, 90, 90, 30))  # 设置位置和大小
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # 创建按钮
        ### 保存用户名按钮
        self.user_conf_save_button = QPushButton("save", self.centralwidget)
        self.user_conf_save_button.setGeometry(QtCore.QRect(310, 50, 60, 30))
        self.user_conf_save_button.clicked.connect(self.save_user)

        ### 保存下载路径按钮
        self.path_conf_save_button = QPushButton("save", self.centralwidget)
        self.path_conf_save_button.setGeometry(QtCore.QRect(310, 10, 60, 30))
        self.path_conf_save_button.clicked.connect(self.save_download_path)

        ### 下载按钮
        self.down_start_button = QPushButton("start down", self.centralwidget)
        self.down_start_button.setGeometry(QtCore.QRect(10, 150, 80, 30))
        self.down_start_button.clicked.connect(self.down_start)

        # self.down_stop_button = QPushButton("stop down", self.centralwidget)
        # self.down_stop_button.setGeometry(QtCore.QRect(290, 100, 81, 31))
        # self.down_stop_button.clicked.connect(self.down_start)

        # 配置读取的配置信息
        self.conf = ReadConf()
        self.set_data()

        # 设置命名方式值
        folder_for_name = self.conf.read_name()
        if folder_for_name == '标题命名':
            self.folder_name_type_combo_box.setCurrentIndex(1)

    def on_combo_changed(self, text):
        self.conf.write_name(text)

    def set_data(self):
        user_info = self.conf.read_asmr_user()
        download_path = self.conf.read_download_conf()
        speed_limit = str(download_path[0])
        self.user_name.setText(user_info['username'])
        self.password.setText(user_info['passwd'])
        self.speed_limit.setText(speed_limit)
        self.down_path.setText(download_path[1])

    def save_download_path(self):
        download_path = self.down_path.text()
        speed_limit = self.speed_limit.text()
        self.conf.write_download_conf(speed_limit, download_path)

    def save_user(self):
        from src.asmr_api.login import login
        user_name = self.user_name.text()
        password = self.password.text()
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
        self.download_thread = DownloadThread()
        self.download_thread.start()  # 启动后台下载线程
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLineEdit,
    QMessageBox,
    QComboBox,
    QLabel,
    QCheckBox,
    QFileDialog,
)
from PyQt6 import QtCore, QtWidgets
from src.asmr_api.get_asmr_works import get_asmr_downlist_api
from src.read_conf import ReadConf


class DownloadThread(QThread):
    download_finished = pyqtSignal(str)
    download_progress = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._is_running = True  # 控制线程是否运行

    def run(self):
        while self._is_running:
            try:
                get_asmr_downlist_api()  # 执行下载操作
                self.download_finished.emit("下载完成")
                break
            except Exception as e:
                print(e)
                self.download_finished.emit(f"发生错误: {str(e)}")
                break

    def stop(self):
        self._is_running = False  # 设置停止标志


class INDEX(QMainWindow):
    def __init__(self):
        super().__init__()

        # 配置读取
        self.conf = ReadConf()
        self.selected_formats = self.conf.read_downfile_type()


        # 创建界面组件
        self.setWindowTitle("ASMR_download")
        self.setGeometry(100, 100, 400, 250)

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

        # 文件命名方式标签
        self.label = QLabel("文件夹命名方式", self.centralwidget)
        self.label.setGeometry(QtCore.QRect(10, 90, 90, 30))
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # 选择性下载
        self.checkbox_MP3 = QCheckBox("MP3", self.centralwidget)
        self.checkbox_MP3.setGeometry(QtCore.QRect(10, 130, 60, 30))
        self.checkbox_MP3.setChecked(self.selected_formats["MP3"])
        self.checkbox_MP3.toggled.connect(self.update_checkbox_MP3)

        self.checkbox_MP4 = QCheckBox("MP4", self.centralwidget)
        self.checkbox_MP4.setGeometry(QtCore.QRect(70, 130, 60, 30))
        self.checkbox_MP4.setChecked(self.selected_formats["MP4"])
        self.checkbox_MP4.toggled.connect(self.update_checkbox_MP4)

        self.checkbox_FLAC = QCheckBox("FLAC", self.centralwidget)
        self.checkbox_FLAC.setGeometry(QtCore.QRect(130, 130, 60, 30))
        self.checkbox_FLAC.setChecked(self.selected_formats["FLAC"])
        self.checkbox_FLAC.toggled.connect(self.update_checkbox_FLAC)

        self.checkbox_WAV = QCheckBox("WAV", self.centralwidget)
        self.checkbox_WAV.setGeometry(QtCore.QRect(190, 130, 60, 30))
        self.checkbox_WAV.setChecked(self.selected_formats["WAV"])
        self.checkbox_WAV.toggled.connect(self.update_checkbox_WAV)

        self.checkbox_JPG = QCheckBox("JPG", self.centralwidget)
        self.checkbox_JPG.setGeometry(QtCore.QRect(250, 130, 60, 30))
        self.checkbox_JPG.setChecked(self.selected_formats["JPG"])
        self.checkbox_JPG.toggled.connect(self.update_checkbox_JPG)

        self.checkbox_PNG = QCheckBox("PNG", self.centralwidget)
        self.checkbox_PNG.setGeometry(QtCore.QRect(310, 130, 60, 30))
        self.checkbox_PNG.setChecked(self.selected_formats["PNG"])
        self.checkbox_PNG.toggled.connect(self.update_checkbox_PNG)

        self.checkbox_PDF = QCheckBox("PDF", self.centralwidget)
        self.checkbox_PDF.setGeometry(QtCore.QRect(10, 150, 60, 30))
        self.checkbox_PDF.setChecked(self.selected_formats["PDF"])
        self.checkbox_PDF.toggled.connect(self.update_checkbox_PDF)

        self.checkbox_TXT = QCheckBox("TXT", self.centralwidget)
        self.checkbox_TXT.setGeometry(QtCore.QRect(70, 150, 60, 30))
        self.checkbox_TXT.setChecked(self.selected_formats["TXT"])
        self.checkbox_TXT.toggled.connect(self.update_checkbox_TXT)

        self.checkbox_VTT = QCheckBox("VTT", self.centralwidget)
        self.checkbox_VTT.setGeometry(QtCore.QRect(130, 150, 60, 30))
        self.checkbox_VTT.setChecked(self.selected_formats["VTT"])
        self.checkbox_VTT.toggled.connect(self.update_checkbox_VTT)

        self.checkbox_VTT = QCheckBox("LRC", self.centralwidget)
        self.checkbox_VTT.setGeometry(QtCore.QRect(190, 150, 60, 30))
        self.checkbox_VTT.setChecked(self.selected_formats["LRC"])
        self.checkbox_VTT.toggled.connect(self.update_checkbox_LCR)

        # 创建按钮
        self.user_conf_save_button = QPushButton("save", self.centralwidget)
        self.user_conf_save_button.setGeometry(QtCore.QRect(310, 50, 60, 30))
        self.user_conf_save_button.clicked.connect(self.save_user)

        self.path_conf_save_button = QPushButton("save", self.centralwidget)
        self.path_conf_save_button.setGeometry(QtCore.QRect(310, 10, 60, 30))
        self.path_conf_save_button.clicked.connect(self.save_download_path)

        self.down_start_button = QPushButton("start down", self.centralwidget)
        self.down_start_button.setGeometry(QtCore.QRect(10, 200, 80, 30))
        self.down_start_button.clicked.connect(self.down_start)

        self.set_data()

    def update_checkbox_MP3(self):
        if self.selected_formats['MP3']:
            self.conf.write_downfile_type_MP3('MP3', 'false')
        else:
            self.conf.write_downfile_type_MP3('MP3', 'true')
    def update_checkbox_MP4(self):
        if self.selected_formats['MP4']:
            self.conf.write_downfile_type_MP3('MP4','false')
        else:
            self.conf.write_downfile_type_MP3('MP4', 'true')
    def update_checkbox_FLAC(self):
        if self.selected_formats['FLAC']:
            self.conf.write_downfile_type_MP3('FLAC', 'false')
        else:
            self.conf.write_downfile_type_MP3('FLAC', 'true')
    def update_checkbox_WAV(self):
        if self.selected_formats['WAV']:
            self.conf.write_downfile_type_MP3('WAV', 'false')
        else:
            self.conf.write_downfile_type_MP3('WAV', 'true')
    def update_checkbox_JPG(self):
        if self.selected_formats['JPG']:
            self.conf.write_downfile_type_MP3('JPG', 'false')
        else:
            self.conf.write_downfile_type_MP3('JPG', 'true')
    def update_checkbox_PNG(self):
        if self.selected_formats['PNG']:
            self.conf.write_downfile_type_MP3('PNG', 'false')
        else:
            self.conf.write_downfile_type_MP3('PNG', 'true')
    def update_checkbox_PDF(self):
        if self.selected_formats['PDF']:
            self.conf.write_downfile_type_MP3('PDF', 'false')
        else:
            self.conf.write_downfile_type_MP3('PDF', 'true')
    def update_checkbox_TXT(self):
        if self.selected_formats['TXT']:
            self.conf.write_downfile_type_MP3('TXT', 'false')
        else:
            self.conf.write_downfile_type_MP3('TXT', 'true')
    def update_checkbox_VTT(self):
        if self.selected_formats['VTT']:
            self.conf.write_downfile_type_MP3('VTT', 'false')
        else:
            self.conf.write_downfile_type_MP3('VTT', 'true')
    def update_checkbox_LCR(self):
        if self.selected_formats['LRC']:
            self.conf.write_downfile_type_MP3('LRC', 'false')
        else:
            self.conf.write_downfile_type_MP3('LRC', 'true')


    def on_combo_changed(self, text):
        self.conf.write_name(text)

    def set_data(self):
        user_info = self.conf.read_asmr_user()
        download_path = self.conf.read_download_conf()
        speed_limit = str(download_path[0])
        self.user_name.setText(user_info["username"])
        self.password.setText(user_info["passwd"])
        self.speed_limit.setText(speed_limit)
        self.down_path.setText(download_path[1])
        # 设置命名方式值
        folder_for_name = self.conf.read_name()
        if folder_for_name == "标题命名":
            self.folder_name_type_combo_box.setCurrentIndex(1)


    def save_download_path(self):
        download_path = QFileDialog.getExistingDirectory(self, "选择下载路径")
        if download_path:
            self.down_path.setText(download_path)
            speed_limit = self.speed_limit.text()
            self.conf.write_download_conf(speed_limit, download_path)

    def save_user(self):
        from src.asmr_api.login import login

        user_name = self.user_name.text()
        password = self.password.text()
        self.conf.write_asmr_username(user_name, password)
        message = login()
        if message is not True:
            self.show_message_box(message, "from asmr.one")

    def show_message_box(self, message, message_from):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(message)
        msg.setWindowTitle(message_from)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        msg.exec()

    def down_start(self):
        self.download_thread = DownloadThread()
        self.download_thread.download_finished.connect(self.on_download_finished)
        self.download_thread.finished.connect(self.download_thread.deleteLater)
        self.download_thread.start()

    def on_download_finished(self, message):
        self.show_message_box(message, "下载完成")
import sys
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt6.uic import loadUi
from src.asmr_api.get_asmr_works import get_asmr_downlist_api



class AddToQueueThread(QThread):
    # 定义一个信号，用来通知主线程任务完成
    finished = pyqtSignal(str)

    def __init__(self, keyword):
        super().__init__()
        self.keyword = keyword

    def run(self):
        # 在这个线程中调用down.add_list
        self.finished.emit(f"已将 '{self.keyword}' 添加到下载列表")  # 发出信号通知主线程任务完成
        get_asmr_downlist_api(self.keyword)
        self.finished.emit(f" '{self.keyword}' 下载完成")

class INDEX(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi('src/UI/index.ui', self)  # 加载.ui文件

        # 连接信号到方法
        self.add_queue.clicked.connect(self.add_to_queue)
        self.down_path_save.clicked.connect(self.save_download_path)

    def add_to_queue(self):
        keyword = self.keyword.text()  # 获取输入的关键字
        if keyword:
            # 创建并启动后台线程
            self.thread = AddToQueueThread(keyword)
            self.thread.finished.connect(self.update_output)  # 连接信号，任务完成后更新输出
            self.thread.start()
        else:
            self.cli_output.append("未输入关键字")  # 如果没有输入，提示用户

    def update_output(self, message):
        # 更新CLI输出区域，显示后台线程返回的消息
        self.cli_output.append(message)

    def save_download_path(self):
        download_path = self.down_path.text()  # 获取下载路径
        if download_path:
            self.cli_output.append(f"已保存下载路径: {download_path}")
        else:
            self.cli_output.append("未输入下载路径")

        # 允许用户选择文件夹作为下载路径
        folder = QFileDialog.getExistingDirectory(self, "选择下载文件夹")
        if folder:
            self.down_path.setText(folder)
            self.cli_output.append(f"新下载路径: {folder}")
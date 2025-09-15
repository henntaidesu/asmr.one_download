import re
import os
import time
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QListWidget, QListWidgetItem, QMessageBox,
    QScrollArea, QFrame
)
from PyQt6 import QtCore, QtWidgets
from src.asmr_api.get_down_list import get_down_list
from src.asmr_api.get_work_detail import get_work_detail
from src.download.download_thread import MultiFileDownloadManager
from src.read_conf import ReadConf


class WorkDetailThread(QThread):
    detail_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, work_id):
        super().__init__()
        self.work_id = work_id

    def run(self):
        try:
            detail = get_work_detail(self.work_id)
            self.detail_loaded.emit(detail)
        except Exception as e:
            self.error_occurred.emit(str(e))


class DownloadItemWidget(QWidget):
    download_paused = pyqtSignal(str)
    download_resumed = pyqtSignal(str)
    download_cancelled = pyqtSignal(str)
    download_started = pyqtSignal(str, dict)
    detail_ready = pyqtSignal()

    def __init__(self, work_info):
        super().__init__()
        self.work_info = work_info
        self.work_detail = None
        self.is_paused = False
        self.is_downloading = False
        self.download_speed = 0.0  # KB/s
        self.bytes_downloaded = 0
        self.total_bytes = 0
        self.last_update_time = time.time()
        self.last_downloaded = 0
        self.setup_ui()
        self.load_work_detail()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        # 顶部信息行
        info_layout = QHBoxLayout()

        # 作品标题
        self.title_label = QLabel(self.work_info['title'])
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.title_label.setWordWrap(True)
        info_layout.addWidget(self.title_label, 1)

        # RJ号
        self.rj_label = QLabel(f"RJ{self.work_info['id']:06d}")
        self.rj_label.setStyleSheet("color: #666; font-size: 12px;")
        info_layout.addWidget(self.rj_label)

        layout.addLayout(info_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 底部信息和按钮
        bottom_layout = QHBoxLayout()

        # 状态标签
        self.status_label = QLabel("等待下载")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        bottom_layout.addWidget(self.status_label)

        # 下载速度标签
        self.speed_label = QLabel("0 KB/s")
        self.speed_label.setStyleSheet("color: #0066cc; font-size: 11px; font-weight: bold;")
        bottom_layout.addWidget(self.speed_label)

        # 文件大小标签
        self.size_label = QLabel("获取中...")
        self.size_label.setStyleSheet("color: #666; font-size: 11px;")
        bottom_layout.addWidget(self.size_label)

        bottom_layout.addStretch()

        # 控制按钮
        self.start_button = QPushButton("开始")
        self.start_button.setFixedSize(60, 25)
        self.start_button.clicked.connect(self.start_download)
        self.start_button.setEnabled(False)
        bottom_layout.addWidget(self.start_button)

        self.pause_button = QPushButton("暂停")
        self.pause_button.setFixedSize(60, 25)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.pause_button.setEnabled(False)
        bottom_layout.addWidget(self.pause_button)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.setFixedSize(60, 25)
        self.cancel_button.clicked.connect(self.cancel_download)
        bottom_layout.addWidget(self.cancel_button)

        layout.addLayout(bottom_layout)

        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #ddd;")
        layout.addWidget(line)

        self.setLayout(layout)

    def load_work_detail(self):
        """加载作品详细信息"""
        self.detail_thread = WorkDetailThread(self.work_info['id'])
        self.detail_thread.detail_loaded.connect(self.on_detail_loaded)
        self.detail_thread.error_occurred.connect(self.on_detail_error)
        self.detail_thread.start()

    def on_detail_loaded(self, work_detail):
        """作品详细信息加载完成"""
        self.work_detail = work_detail
        if work_detail:
            total_mb = work_detail['total_size'] / (1024 * 1024)
            self.size_label.setText(f"0/{total_mb:.1f} MB")
            self.start_button.setEnabled(True)
            self.status_label.setText(f"准备下载 ({len(work_detail['files'])} 个文件)")
            # 通知父窗口检查是否可以启用全局开始按钮
            self.detail_ready.emit()
        else:
            self.size_label.setText("获取失败")
            self.status_label.setText("获取文件信息失败")

    def on_detail_error(self, error_msg):
        """作品详细信息加载错误"""
        self.size_label.setText("获取失败")
        self.status_label.setText(f"错误: {error_msg}")

    def start_download(self):
        """开始下载"""
        if not self.work_detail:
            return

        self.is_downloading = True
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.status_label.setText("下载中...")
        self.download_started.emit(str(self.work_info['id']), self.work_detail)

    def toggle_pause(self):
        if self.is_paused:
            self.resume_download()
        else:
            self.pause_download()

    def pause_download(self):
        self.is_paused = True
        self.pause_button.setText("继续")
        self.status_label.setText("已暂停")
        self.speed_label.setText("0 KB/s")
        self.download_paused.emit(str(self.work_info['id']))

    def resume_download(self):
        self.is_paused = False
        self.pause_button.setText("暂停")
        self.status_label.setText("下载中...")
        self.download_resumed.emit(str(self.work_info['id']))

    def cancel_download(self):
        self.status_label.setText("已取消")
        self.speed_label.setText("0 KB/s")
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.is_downloading = False
        self.download_cancelled.emit(str(self.work_info['id']))

    def update_progress(self, progress, downloaded_bytes=0, total_bytes=0, status="下载中..."):
        self.progress_bar.setValue(progress)

        # 更新下载量信息
        if total_bytes > 0:
            self.bytes_downloaded = downloaded_bytes
            self.total_bytes = total_bytes

            # 更新文件大小显示
            downloaded_mb = downloaded_bytes / (1024 * 1024)
            total_mb = total_bytes / (1024 * 1024)
            self.size_label.setText(f"{downloaded_mb:.1f}/{total_mb:.1f} MB")

        if not self.is_paused:
            self.status_label.setText(status)

        if progress == 100:
            self.status_label.setText("下载完成")
            self.speed_label.setText("0 KB/s")
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            self.is_downloading = False

    def update_speed(self, speed_kbps):
        """更新下载速度显示"""
        self.download_speed = speed_kbps
        if speed_kbps >= 1024:
            self.speed_label.setText(f"{speed_kbps/1024:.1f} MB/s")
        else:
            self.speed_label.setText(f"{speed_kbps:.1f} KB/s")

    def set_downloading(self):
        self.status_label.setText("下载中...")
        self.pause_button.setEnabled(True)

    def set_error(self, error_msg):
        self.status_label.setText(f"错误: {error_msg}")
        self.speed_label.setText("0 KB/s")
        self.pause_button.setEnabled(False)
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #ff6b6b; }")

    def format_bytes(self, bytes_value):
        """格式化字节数为可读格式"""
        if bytes_value >= 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024 * 1024):.1f} GB"
        elif bytes_value >= 1024 * 1024:
            return f"{bytes_value / (1024 * 1024):.1f} MB"
        elif bytes_value >= 1024:
            return f"{bytes_value / 1024:.1f} KB"
        else:
            return f"{bytes_value} B"


class DownloadListThread(QThread):
    list_updated = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            works_list = get_down_list()
            if works_list:
                self.list_updated.emit(works_list)
            else:
                self.error_occurred.emit("未获取到下载列表")
        except Exception as e:
            self.error_occurred.emit(f"获取下载列表失败: {str(e)}")


class DownloadPage(QWidget):
    def __init__(self):
        super().__init__()
        self.conf = ReadConf()
        self.download_items = {}
        self.download_manager = None
        self.setup_ui()
        self.setup_download_manager()
        self.load_download_list()


    def setup_ui(self):
        self.setWindowTitle("下载列表")
        self.setFixedSize(700, 500)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # 顶部控制栏
        top_layout = QHBoxLayout()

        # 标题
        title_label = QLabel("下载列表")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        top_layout.addWidget(title_label)

        top_layout.addStretch()

        # 全局速度显示
        self.global_speed_label = QLabel("总速度: 0 KB/s")
        self.global_speed_label.setStyleSheet("color: #0066cc; font-weight: bold;")
        top_layout.addWidget(self.global_speed_label)

        # 开始下载按钮
        self.start_all_button = QPushButton("开始下载")
        self.start_all_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.start_all_button.clicked.connect(self.start_sequential_downloads)
        self.start_all_button.setEnabled(False)
        top_layout.addWidget(self.start_all_button)

        # 刷新按钮
        self.refresh_button = QPushButton("刷新列表")
        self.refresh_button.clicked.connect(self.load_download_list)
        top_layout.addWidget(self.refresh_button)

        # 全部暂停按钮
        self.pause_all_button = QPushButton("全部暂停")
        self.pause_all_button.clicked.connect(self.pause_all_downloads)
        top_layout.addWidget(self.pause_all_button)

        # 设置按钮
        self.settings_button = QPushButton("设置")
        self.settings_button.clicked.connect(self.open_settings)
        top_layout.addWidget(self.settings_button)

        layout.addLayout(top_layout)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 下载列表容器
        self.download_container = QWidget()
        self.download_layout = QVBoxLayout(self.download_container)
        self.download_layout.setContentsMargins(0, 0, 0, 0)
        self.download_layout.addStretch()

        scroll.setWidget(self.download_container)
        layout.addWidget(scroll)

        # 底部状态栏
        status_layout = QHBoxLayout()
        self.status_label = QLabel("准备就绪")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.count_label = QLabel("总数: 0")
        self.count_label.setStyleSheet("color: #666; font-size: 11px;")
        status_layout.addWidget(self.count_label)

        layout.addLayout(status_layout)

        self.setLayout(layout)

    def setup_download_manager(self):
        """设置下载管理器"""
        download_dir = "./downloads"  # 默认下载目录
        os.makedirs(download_dir, exist_ok=True)  # 确保下载目录存在
        self.download_manager = MultiFileDownloadManager(download_dir)

        # 连接下载管理器信号
        self.download_manager.download_started.connect(self.on_download_started)
        self.download_manager.download_progress.connect(self.on_download_progress)
        self.download_manager.download_completed.connect(self.on_download_completed)
        self.download_manager.download_failed.connect(self.on_download_failed)
        self.download_manager.speed_updated.connect(self.on_speed_updated)

        self.download_manager.start()

    def load_download_list(self):
        self.status_label.setText("正在获取下载列表...")
        self.refresh_button.setEnabled(False)

        self.list_thread = DownloadListThread()
        self.list_thread.list_updated.connect(self.on_list_updated)
        self.list_thread.error_occurred.connect(self.on_list_error)
        self.list_thread.finished.connect(lambda: self.refresh_button.setEnabled(True))
        self.list_thread.start()

    def on_list_updated(self, works_list):
        # 清空现有列表
        self.clear_all_items()

        # 添加新的下载项
        for work in works_list:
            self.add_download_item(work)

        self.count_label.setText(f"总数: {len(works_list)}")
        self.status_label.setText(f"已加载 {len(works_list)} 个下载项")

        # 如果有下载项，启用开始全部下载按钮
        if works_list:
            self.start_all_button.setEnabled(True)

    def on_list_error(self, error_msg):
        self.status_label.setText(f"错误: {error_msg}")
        QMessageBox.warning(self, "错误", error_msg)

    def add_download_item(self, work_info):
        item_widget = DownloadItemWidget(work_info)
        item_widget.download_paused.connect(self.on_download_paused)
        item_widget.download_resumed.connect(self.on_download_resumed)
        item_widget.download_cancelled.connect(self.on_download_cancelled)
        item_widget.download_started.connect(self.on_item_download_started)
        item_widget.detail_ready.connect(self.check_start_all_button)

        # 插入到倒数第二个位置（最后一个是stretch）
        self.download_layout.insertWidget(self.download_layout.count() - 1, item_widget)

        self.download_items[str(work_info['id'])] = item_widget

    def clear_all_items(self):
        # 清空所有下载项
        for item_id in list(self.download_items.keys()):
            item = self.download_items[item_id]
            self.download_layout.removeWidget(item)
            item.deleteLater()
            del self.download_items[item_id]

    def on_item_download_started(self, work_id, work_detail):
        """处理单个项目开始下载"""
        if self.download_manager:
            self.download_manager.add_download(int(work_id), work_detail)
            self.download_manager.start_next_download()

    def on_download_started(self, work_id):
        """下载开始"""
        print(f"开始下载: {work_id}")

    def on_download_progress(self, work_id, progress, downloaded, total, status):
        """下载进度更新"""
        if work_id in self.download_items:
            self.download_items[work_id].update_progress(progress, downloaded, total, status)

    def on_download_completed(self, work_id):
        """下载完成"""
        print(f"下载完成: {work_id}")
        if work_id in self.download_items:
            self.download_items[work_id].update_progress(100, 0, 0, "下载完成")
        self.update_global_speed()

        # 检查是否还有等待中的下载任务
        if self.download_manager and len(self.download_manager.download_queue) > 0:
            self.status_label.setText(f"下载完成: RJ{work_id}, 继续下一个...")
        else:
            self.status_label.setText("所有下载任务已完成")

    def on_download_failed(self, work_id, error):
        """下载失败"""
        if work_id in self.download_items:
            self.download_items[work_id].set_error(error)
        self.update_global_speed()

    def on_speed_updated(self, work_id, speed_kbps):
        """速度更新"""
        if work_id in self.download_items:
            self.download_items[work_id].update_speed(speed_kbps)
        self.update_global_speed()

    def on_download_paused(self, item_id):
        print(f"暂停下载: {item_id}")
        if self.download_manager:
            self.download_manager.pause_download(item_id)
        self.update_global_speed()

    def on_download_resumed(self, item_id):
        print(f"继续下载: {item_id}")
        if self.download_manager:
            self.download_manager.resume_download(item_id)

    def on_download_cancelled(self, item_id):
        print(f"取消下载: {item_id}")
        if self.download_manager:
            self.download_manager.cancel_download(item_id)
        self.update_global_speed()

    def check_start_all_button(self):
        """检查是否应该启用开始全部下载按钮"""
        ready_count = 0
        for item in self.download_items.values():
            if item.work_detail and item.start_button.isEnabled() and not item.is_downloading:
                ready_count += 1

        # 如果有准备好的下载项，启用按钮
        self.start_all_button.setEnabled(ready_count > 0)

    def start_sequential_downloads(self):
        """按顺序开始下载"""
        # 获取所有准备好的下载项，按添加顺序排列
        ready_items = []
        for i in range(self.download_layout.count() - 1):  # 排除最后的stretch
            widget = self.download_layout.itemAt(i).widget()
            if isinstance(widget, DownloadItemWidget):
                if (not widget.is_downloading and
                    widget.start_button.isEnabled() and
                    widget.work_detail):
                    ready_items.append(widget)

        if ready_items:
            # 开始第一个下载
            first_item = ready_items[0]
            first_item.start_download()

            # 将剩余的添加到队列
            for item in ready_items[1:]:
                if self.download_manager:
                    self.download_manager.add_download(int(item.work_info['id']), item.work_detail)

            self.status_label.setText(f"开始按顺序下载，共 {len(ready_items)} 个任务")
        else:
            self.status_label.setText("没有可开始的下载任务")

    def pause_all_downloads(self):
        for item_id, item in self.download_items.items():
            if item.is_downloading and not item.is_paused and item.pause_button.isEnabled():
                item.pause_download()
                if self.download_manager:
                    self.download_manager.pause_download(item_id)


    def open_settings(self):
        """打开设置页面"""
        from src.UI.index import INDEX
        if not hasattr(self, 'settings_page') or not self.settings_page:
            self.settings_page = INDEX()
        self.settings_page.show()
        self.settings_page.raise_()
        self.settings_page.activateWindow()

    def update_global_speed(self):
        """更新全局下载速度"""
        total_speed = 0.0
        for item in self.download_items.values():
            if item.is_downloading and not item.is_paused:
                total_speed += item.download_speed

        if total_speed >= 1024:
            self.global_speed_label.setText(f"总速度: {total_speed/1024:.1f} MB/s")
        else:
            self.global_speed_label.setText(f"总速度: {total_speed:.1f} KB/s")
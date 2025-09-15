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
from src.read_conf import ReadConf


class DownloadItemWidget(QWidget):
    download_paused = pyqtSignal(str)
    download_resumed = pyqtSignal(str)
    download_cancelled = pyqtSignal(str)

    def __init__(self, work_info):
        super().__init__()
        self.work_info = work_info
        self.is_paused = False
        self.download_speed = 0.0  # KB/s
        self.bytes_downloaded = 0
        self.total_bytes = 0
        self.last_update_time = time.time()
        self.last_downloaded = 0
        # 为模拟分配固定的文件大小
        import random
        self.simulated_total_bytes = random.randint(50, 200) * 1024 * 1024  # 50-200MB
        self.setup_ui()

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
        self.size_label = QLabel("0/0 MB")
        self.size_label.setStyleSheet("color: #666; font-size: 11px;")
        bottom_layout.addWidget(self.size_label)

        bottom_layout.addStretch()

        # 控制按钮
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
        self.pause_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.download_cancelled.emit(str(self.work_info['id']))

    def update_progress(self, progress, downloaded_bytes=0, total_bytes=0, status="下载中..."):
        self.progress_bar.setValue(progress)

        # 更新下载量信息
        if total_bytes > 0:
            self.bytes_downloaded = downloaded_bytes
            self.total_bytes = total_bytes

            # 计算下载速度
            current_time = time.time()
            time_diff = current_time - self.last_update_time

            # 确保有足够的时间间隔来计算速度（至少0.1秒）
            if time_diff >= 0.1 and downloaded_bytes > self.last_downloaded:
                bytes_diff = downloaded_bytes - self.last_downloaded
                speed_bps = bytes_diff / time_diff
                self.download_speed = speed_bps / 1024  # 转换为 KB/s

                # 更新速度显示
                if self.download_speed >= 1024:
                    self.speed_label.setText(f"{self.download_speed/1024:.1f} MB/s")
                else:
                    self.speed_label.setText(f"{self.download_speed:.1f} KB/s")

                self.last_update_time = current_time
                self.last_downloaded = downloaded_bytes
            elif downloaded_bytes == self.last_downloaded and time_diff > 2:
                # 如果下载停滞超过2秒，显示0速度
                self.download_speed = 0
                self.speed_label.setText("0 KB/s")

            # 更新文件大小显示
            downloaded_mb = downloaded_bytes / (1024 * 1024)
            total_mb = total_bytes / (1024 * 1024)
            self.size_label.setText(f"{downloaded_mb:.1f}/{total_mb:.1f} MB")

        if not self.is_paused:
            self.status_label.setText(status)

        if progress == 100:
            self.status_label.setText("下载完成")
            self.speed_label.setText("0 KB/s")
            self.pause_button.setEnabled(False)
            self.cancel_button.setEnabled(False)

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
        self.setup_ui()
        self.load_download_list()

        # 定时器用于模拟进度更新
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.simulate_progress)

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

        # 刷新按钮
        self.refresh_button = QPushButton("刷新列表")
        self.refresh_button.clicked.connect(self.load_download_list)
        top_layout.addWidget(self.refresh_button)

        # 全部暂停按钮
        self.pause_all_button = QPushButton("全部暂停")
        self.pause_all_button.clicked.connect(self.pause_all_downloads)
        top_layout.addWidget(self.pause_all_button)

        # 清空列表按钮
        self.clear_button = QPushButton("清空列表")
        self.clear_button.clicked.connect(self.clear_completed)
        top_layout.addWidget(self.clear_button)

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

    def on_list_error(self, error_msg):
        self.status_label.setText(f"错误: {error_msg}")
        QMessageBox.warning(self, "错误", error_msg)

    def add_download_item(self, work_info):
        item_widget = DownloadItemWidget(work_info)
        item_widget.download_paused.connect(self.on_download_paused)
        item_widget.download_resumed.connect(self.on_download_resumed)
        item_widget.download_cancelled.connect(self.on_download_cancelled)

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

    def on_download_paused(self, item_id):
        print(f"暂停下载: {item_id}")
        self.update_global_speed()

    def on_download_resumed(self, item_id):
        print(f"继续下载: {item_id}")

    def on_download_cancelled(self, item_id):
        print(f"取消下载: {item_id}")
        self.update_global_speed()

    def pause_all_downloads(self):
        for item in self.download_items.values():
            if not item.is_paused and item.pause_button.isEnabled():
                item.pause_download()

    def clear_completed(self):
        # 移除已完成或已取消的下载项
        to_remove = []
        for item_id, item in self.download_items.items():
            if item.progress_bar.value() == 100 or not item.cancel_button.isEnabled():
                to_remove.append(item_id)

        for item_id in to_remove:
            item = self.download_items[item_id]
            self.download_layout.removeWidget(item)
            item.deleteLater()
            del self.download_items[item_id]

        self.count_label.setText(f"总数: {len(self.download_items)}")

    def update_global_speed(self):
        """更新全局下载速度"""
        total_speed = 0.0
        for item in self.download_items.values():
            if not item.is_paused and item.pause_button.isEnabled():
                total_speed += item.download_speed

        if total_speed >= 1024:
            self.global_speed_label.setText(f"总速度: {total_speed/1024:.1f} MB/s")
        else:
            self.global_speed_label.setText(f"总速度: {total_speed:.1f} KB/s")

    def simulate_progress(self):
        # 模拟下载进度（用于演示）
        import random
        for item in self.download_items.values():
            if item.pause_button.isEnabled() and not item.is_paused:
                current = item.progress_bar.value()
                if current < 100:
                    # 模拟现实的下载速度（100KB/s - 5MB/s）
                    simulate_speed_kbs = random.uniform(100, 5120)  # KB/s
                    simulate_bytes_per_second = simulate_speed_kbs * 1024  # 转换为 bytes/s

                    # 计算1秒内应该下载的字节数
                    bytes_increment = int(simulate_bytes_per_second)

                    # 使用固定的总文件大小
                    total_bytes = item.simulated_total_bytes

                    # 计算当前已下载字节数
                    if not hasattr(item, 'simulated_downloaded'):
                        item.simulated_downloaded = 0

                    # 增加下载字节数，但不超过总大小
                    item.simulated_downloaded = min(
                        item.simulated_downloaded + bytes_increment,
                        total_bytes
                    )

                    # 计算进度百分比
                    new_progress = int(item.simulated_downloaded * 100 / total_bytes)

                    # 更新进度
                    item.update_progress(new_progress, item.simulated_downloaded, total_bytes)

        self.update_global_speed()

    def start_simulation(self):
        # 启动进度模拟（仅用于演示）
        if self.download_items:
            for item in self.download_items.values():
                item.set_downloading()
            self.progress_timer.start(1000)  # 每秒更新一次

    def stop_simulation(self):
        self.progress_timer.stop()
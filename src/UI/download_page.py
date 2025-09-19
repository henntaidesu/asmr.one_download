import re
import os
import time
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QListWidget, QListWidgetItem, QMessageBox,
    QScrollArea, QFrame, QComboBox
)
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtCore import pyqtSignal
from PyQt6 import QtCore, QtWidgets
from src.asmr_api.get_down_list import get_down_list
from src.asmr_api.get_work_detail import get_work_detail
from src.asmr_api.works_review import review
from src.download.download_thread import MultiFileDownloadManager
from src.read_conf import ReadConf
from src.language.language_manager import language_manager


class FocusedScrollArea(QScrollArea):
    """带有焦点管理的滚动区域"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.WheelFocus)

    def enterEvent(self, event):
        """鼠标进入时获取焦点"""
        self.setFocus()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开时清除焦点"""
        self.clearFocus()
        super().leaveEvent(event)

    def wheelEvent(self, event):
        """处理滚轮事件，只有在有焦点时才处理"""
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            # 如果没有焦点，将事件传递给父控件
            if self.parent():
                self.parent().wheelEvent(event)


class TriangleButton(QLabel):
    """可点击的三角形折叠按钮"""
    clicked = pyqtSignal(str)  # 传递folder_path参数

    def __init__(self, collapsed=True, folder_path=""):
        super().__init__()
        self.collapsed = collapsed
        self.folder_path = folder_path
        self.setFixedSize(12, 12)
        self.update_icon()

    def update_icon(self):
        """更新三角形图标"""
        if self.collapsed:
            self.setText("▶")  # 右指三角形
        else:
            self.setText("▼")  # 下指三角形
        self.setStyleSheet("color: #000; font-size: 10px; font-family: monospace;")

    def mousePressEvent(self, event):
        """处理点击事件"""
        try:
            from PyQt6.QtCore import Qt
            if event.button() == Qt.MouseButton.LeftButton:
                self.collapsed = not self.collapsed
                self.update_icon()
                self.clicked.emit(self.folder_path)
        except RuntimeError:
            # 忽略已删除对象的错误
            pass


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
    detail_ready = pyqtSignal()

    def __init__(self, work_info, parent_page=None):
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
        self.parent_page = parent_page
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
        self.status_label = QLabel(language_manager.get_text('waiting'))
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        bottom_layout.addWidget(self.status_label)

        # 下载速度标签
        self.speed_label = QLabel(f"0 {language_manager.get_text('kb_per_second')}")
        self.speed_label.setStyleSheet("color: #0066cc; font-size: 11px; font-weight: bold;")
        bottom_layout.addWidget(self.speed_label)

        # 文件大小标签
        self.size_label = QLabel(language_manager.get_text('loading'))
        self.size_label.setStyleSheet("color: #666; font-size: 11px;")
        bottom_layout.addWidget(self.size_label)

        bottom_layout.addStretch()

        layout.addLayout(bottom_layout)

        # 文件目录展示区域（初始隐藏）
        self.file_tree_scroll = FocusedScrollArea()
        self.file_tree_scroll.setVisible(False)
        self.file_tree_scroll.setMaximumHeight(250)
        self.file_tree_scroll.setWidgetResizable(True)
        self.file_tree_scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.file_tree_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.file_tree_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 2px;
                margin: 2px 0px;
            }
            QScrollBar:vertical {
                background: #e8e8e8;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #888888;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #888888;
            }
            QScrollBar::handle:vertical:pressed {
                background: #888888;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                background: #e8e8e8;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #888888;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #888888;
            }
            QScrollBar::handle:horizontal:pressed {
                background: #888888;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)

        self.file_tree_widget = QWidget()
        self.file_tree_layout = QVBoxLayout()
        self.file_tree_layout.setContentsMargins(5, 5, 5, 5)
        self.file_tree_layout.setSpacing(1)
        self.file_tree_widget.setLayout(self.file_tree_layout)

        self.file_tree_scroll.setWidget(self.file_tree_widget)

        layout.addWidget(self.file_tree_scroll)

        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #ddd;")
        layout.addWidget(line)

        # 添加点击事件处理
        self.is_expanded = False
        self.collapsed_folders = set()  # 存储被折叠的文件夹路径
        self.installEventFilter(self)

        self.setLayout(layout)

    def eventFilter(self, obj, event):
        """处理点击事件"""
        from PyQt6.QtCore import QEvent
        from PyQt6.QtGui import QMouseEvent
        from PyQt6.QtCore import Qt

        if obj == self and event.type() == QEvent.Type.MouseButtonPress:
            if isinstance(event, QMouseEvent) and event.button() == Qt.MouseButton.LeftButton:
                # 检查点击位置是否在展开区域内
                click_pos = event.position().toPoint()

                # 如果展开区域可见，检查点击是否在其范围内
                if self.file_tree_scroll.isVisible():
                    scroll_geometry = self.file_tree_scroll.geometry()
                    if scroll_geometry.contains(click_pos):
                        # 点击在展开区域内，不处理
                        return False

                # 点击在主区域，处理展开/收起逻辑
                self.handle_item_click()
                return True
        return super().eventFilter(obj, event)

    def handle_item_click(self):
        """处理点击事件，包括收起其他展开项"""
        if not self.work_detail:
            return

        # 如果有父页面引用，先收起所有其他展开的项
        if self.parent_page:
            self.parent_page.collapse_all_except(self)

        # 切换当前项的展开状态
        self.toggle_file_tree()

    def toggle_file_tree(self):
        """切换文件目录显示状态"""
        if not self.work_detail:
            return

        self.is_expanded = not self.is_expanded

        if self.is_expanded:
            self.build_file_tree()
            self.file_tree_scroll.setVisible(True)
        else:
            self.file_tree_scroll.setVisible(False)

    def collapse_tree(self):
        """收起文件树"""
        self.is_expanded = False
        self.file_tree_scroll.setVisible(False)

    def build_file_tree(self):
        """构建文件目录树"""
        # 清除现有内容
        for i in reversed(range(self.file_tree_layout.count())):
            child = self.file_tree_layout.itemAt(i).widget()
            if child:
                child.setParent(None)

        if not self.work_detail or 'files' not in self.work_detail:
            return

        # 获取文件类型配置
        from src.read_conf import ReadConf
        conf = ReadConf()
        selected_formats = conf.read_downfile_type()

        # 构建目录结构
        file_tree = {}
        for file_info in self.work_detail['files']:
            file_title = file_info['title']
            folder_path = file_info.get('folder_path', '')

            # 判断文件是否会被跳过
            file_type = file_title[file_title.rfind('.') + 1:].upper()
            is_skipped = not selected_formats.get(file_type, False)

            # 处理文件夹路径
            if folder_path:
                # 分割路径，创建嵌套结构
                path_parts = folder_path.strip('/').split('/')
                current_tree = file_tree

                # 创建文件夹结构
                for part in path_parts:
                    if part not in current_tree:
                        current_tree[part] = {'type': 'folder', 'children': {}}
                    current_tree = current_tree[part]['children']

                # 添加文件到相应文件夹
                current_tree[file_title] = {
                    'type': 'file',
                    'size': file_info.get('size', 0),
                    'skipped': is_skipped
                }
            else:
                # 根目录文件
                file_tree[file_title] = {
                    'type': 'file',
                    'size': file_info.get('size', 0),
                    'skipped': is_skipped
                }

        # 第一次构建时，将所有跳过的文件夹设为折叠状态
        if not hasattr(self, '_initial_collapsed_set'):
            self._set_initial_collapsed_folders(file_tree, "")
            self._initial_collapsed_set = True

        # 显示文件树
        self._display_tree(file_tree, 0)

    def _set_initial_collapsed_folders(self, tree_dict, folder_path):
        """初始化时将所有跳过的文件夹设为折叠状态"""
        for name, item in tree_dict.items():
            if item['type'] == 'folder':
                current_path = f"{folder_path}/{name}" if folder_path else name
                if self._check_all_files_skipped(item['children']):
                    self.collapsed_folders.add(current_path)
                # 递归处理子文件夹
                self._set_initial_collapsed_folders(item['children'], current_path)

    def _display_tree(self, tree_dict, indent_level=0, prefix="", is_last=True, folder_path=""):
        """递归显示文件树，使用tree命令风格"""
        items = list(sorted(tree_dict.items()))

        for i, (name, item) in enumerate(items):
            is_current_last = (i == len(items) - 1)
            current_path = f"{folder_path}/{name}" if folder_path else name

            # 构建树形前缀
            if indent_level == 0:
                tree_prefix = ""
            else:
                tree_prefix = prefix + ("└── " if is_current_last else "├── ")

            if item['type'] == 'folder':
                # 检查文件夹内是否所有文件都被跳过
                all_files_skipped = self._check_all_files_skipped(item['children'])

                if all_files_skipped:
                    # 为跳过的文件夹创建带三角形的布局
                    folder_widget = QWidget()
                    folder_layout = QHBoxLayout()
                    folder_layout.setContentsMargins(0, 0, 0, 0)
                    folder_layout.setSpacing(2)

                    # 添加前缀空格
                    if tree_prefix:
                        prefix_label = QLabel(tree_prefix)
                        prefix_label.setStyleSheet("color: #000; font-size: 10px; font-family: 'Courier New', monospace;")
                        folder_layout.addWidget(prefix_label)

                    # 添加三角形按钮
                    is_collapsed = current_path in self.collapsed_folders
                    triangle = TriangleButton(collapsed=is_collapsed, folder_path=current_path)
                    triangle.clicked.connect(self._toggle_folder)
                    folder_layout.addWidget(triangle)

                    # 添加文件夹名称
                    folder_text = f"{name}/"
                    folder_label = QLabel(folder_text)
                    folder_label.setStyleSheet("""
                        color: #000;
                        font-weight: bold;
                        font-size: 10px;
                        font-family: 'Courier New', monospace;
                        text-decoration: line-through;
                    """)
                    folder_layout.addWidget(folder_label)
                    folder_layout.addStretch()

                    folder_widget.setLayout(folder_layout)
                    self.file_tree_layout.addWidget(folder_widget)

                    # 如果文件夹未被折叠，显示子项
                    if current_path not in self.collapsed_folders:
                        if indent_level == 0:
                            next_prefix = ""
                        else:
                            next_prefix = prefix + ("    " if is_current_last else "│   ")
                        self._display_tree(item['children'], indent_level + 1, next_prefix, is_current_last, current_path)
                else:
                    # 正常文件夹（有文件需要下载）
                    folder_text = f"{tree_prefix}{name}/"
                    folder_label = QLabel(folder_text)
                    folder_label.setStyleSheet("color: #666; font-weight: bold; font-size: 10px; font-family: 'Courier New', monospace;")
                    self.file_tree_layout.addWidget(folder_label)

                    # 递归显示子项
                    if indent_level == 0:
                        next_prefix = ""
                    else:
                        next_prefix = prefix + ("    " if is_current_last else "│   ")
                    self._display_tree(item['children'], indent_level + 1, next_prefix, is_current_last, current_path)
            else:
                # 文件
                file_size = self.format_bytes(item.get('size', 0))
                file_text = f"{tree_prefix}{name} ({file_size})"

                file_label = QLabel(file_text)

                if item.get('skipped', False):
                    # 不下载的文件使用黑色和删除线样式
                    file_label.setStyleSheet("""
                        color: #000;
                        font-size: 10px;
                        font-family: 'Courier New', monospace;
                        text-decoration: line-through;
                    """)
                else:
                    # 下载的文件使用灰色
                    file_label.setStyleSheet("color: #666; font-size: 10px; font-family: 'Courier New', monospace;")

                self.file_tree_layout.addWidget(file_label)

    def _check_all_files_skipped(self, children_dict):
        """递归检查文件夹内所有文件是否都被跳过"""
        for name, item in children_dict.items():
            if item['type'] == 'file':
                if not item.get('skipped', False):
                    return False  # 发现有文件不被跳过
            elif item['type'] == 'folder':
                if not self._check_all_files_skipped(item['children']):
                    return False  # 子文件夹内有文件不被跳过
        return True  # 所有文件都被跳过

    def _toggle_folder(self, folder_path):
        """切换文件夹的折叠状态"""
        if folder_path in self.collapsed_folders:
            self.collapsed_folders.remove(folder_path)
        else:
            self.collapsed_folders.add(folder_path)

        # 重新构建文件树
        self.build_file_tree()

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
            self.update_initial_progress()
            # 通知父窗口检查是否可以启用全局开始按钮
            self.detail_ready.emit()
        else:
            self.size_label.setText(language_manager.get_text('failed_to_get'))
            self.status_label.setText(language_manager.get_text('get_file_info_failed'))

    def update_initial_progress(self):
        """更新初始进度显示"""
        if not self.work_detail:
            return
            
        # 检查已下载的文件并计算初始进度
        actual_total_size = self.calculate_actual_total_size()  # 使用实际下载总大小
        downloaded_size = self.calculate_downloaded_size()

        # 计算初始进度
        initial_progress = int((downloaded_size / actual_total_size) * 100) if actual_total_size > 0 else 0
        self.progress_bar.setValue(initial_progress)

        # 使用统一的format_bytes方法格式化显示
        downloaded_formatted = self.format_bytes(downloaded_size)
        total_size_formatted = self.format_bytes(actual_total_size)
        self.size_label.setText(f"{downloaded_formatted}/{total_size_formatted}")
        
        if initial_progress == 100:
            self.status_label.setText(language_manager.get_text('completed'))
        elif downloaded_size > 0:
            self.status_label.setText(f"{language_manager.get_text('ready_to_download')} - 已下载 {initial_progress}%")
        else:
            self.status_label.setText(f"{language_manager.get_text('ready_to_download')} ({len(self.work_detail['files'])} {language_manager.get_text('files')})")

    def on_detail_error(self, error_msg):
        """作品详细信息加载错误"""
        self.size_label.setText(language_manager.get_text('failed_to_get'))
        self.status_label.setText(f"{language_manager.get_text('error')}: {error_msg}")

    def start_download(self):
        """开始下载（由全局按钮调用）"""
        if not self.work_detail:
            return

        self.is_downloading = True
        self.status_label.setText(language_manager.get_text('downloading'))
        # 重置进度条样式，清除之前的错误状态样式
        self.progress_bar.setStyleSheet("")
        return str(self.work_info['id']), self.work_detail

    def pause_download(self):
        """暂停下载（由全局按钮调用）"""
        if not self.is_downloading:
            return
        self.is_paused = True
        self.status_label.setText(language_manager.get_text('paused'))
        self.speed_label.setText("0 KB/s")

    def resume_download(self):
        """继续下载（由全局按钮调用）"""
        if not self.is_downloading:
            return
        self.is_paused = False
        self.status_label.setText(language_manager.get_text('downloading'))


    def update_progress(self, progress, downloaded_bytes=0, total_bytes=0, status="下载中..."):
        self.progress_bar.setValue(progress)

        # 更新下载量信息，使用实际下载总大小
        if downloaded_bytes >= 0 and self.work_detail:
            # 确保 downloaded_bytes 是数字类型，支持超大数值
            if isinstance(downloaded_bytes, str):
                try:
                    downloaded_bytes = int(downloaded_bytes)
                except ValueError:
                    downloaded_bytes = 0

            self.bytes_downloaded = downloaded_bytes

            # 使用传入的实际下载总大小，如果没有传入则使用API返回的原始大小
            if total_bytes > 0:
                self.total_bytes = total_bytes
                actual_total_size = total_bytes
            else:
                # 如果没有传入total_bytes，说明可能是初始化阶段，使用API原始大小
                actual_total_size = self.work_detail['total_size']
                self.total_bytes = actual_total_size

            # 使用实际下载总大小更新显示
            downloaded_formatted = self.format_bytes(downloaded_bytes)
            total_formatted = self.format_bytes(actual_total_size)
            self.size_label.setText(f"{downloaded_formatted}/{total_formatted}")

        if not self.is_paused:
            self.status_label.setText(status)

        if progress == 100:
            self.status_label.setText(language_manager.get_text('completed'))
            self.speed_label.setText("0 KB/s")
            self.is_downloading = False

    def update_speed(self, speed_kbps):
        """更新下载速度显示"""
        self.download_speed = speed_kbps
        if speed_kbps >= 1024:
            self.speed_label.setText(f"{speed_kbps/1024:.2f} MB/s")
        else:
            self.speed_label.setText(f"{speed_kbps:.1f} KB/s")

    def set_downloading(self):
        self.status_label.setText(language_manager.get_text('downloading'))

    def set_error(self, error_msg):
        self.status_label.setText(f"{language_manager.get_text('error')}: {error_msg}")
        self.speed_label.setText("0 KB/s")
        self.is_downloading = False

    def calculate_actual_total_size(self):
        """计算实际需要下载的文件总大小（排除跳过的文件）"""
        if not self.work_detail:
            return 0

        from src.read_conf import ReadConf
        conf = ReadConf()
        selected_formats = conf.read_downfile_type()

        actual_total_size = 0
        for file_info in self.work_detail['files']:
            file_title = file_info['title']
            file_type = file_title[file_title.rfind('.') + 1:].upper()
            if not selected_formats.get(file_type, False):
                continue  # 跳过不需要的文件类型

            file_size = file_info.get('size', 0)
            if isinstance(file_size, str):
                try:
                    file_size = int(file_size)
                except ValueError:
                    file_size = 0
            actual_total_size += file_size

        return actual_total_size

    def calculate_downloaded_size(self):
        """计算已下载的文件大小"""
        if not self.work_detail:
            return 0

        downloaded_size = 0
        from src.read_conf import ReadConf
        conf = ReadConf()
        download_conf = conf.read_download_conf()

        # 读取文件类型配置
        selected_formats = conf.read_downfile_type()
        download_dir = download_conf['download_path']
        
        # 根据文件夹命名方式获取实际文件夹路径
        folder_for_name = conf.read_name()
        work_title = re.sub(r'[\/\\:\*\?\<\>\|]', '-', self.work_info['title'])
        work_id = self.work_info['id']
        
        if folder_for_name == 'rj_naming':
            folder_name = f'RJ{work_id:08d}' if len(str(work_id)) > 6 else f'RJ{work_id:06d}'
        elif folder_for_name == 'title_naming':
            folder_name = work_title
        elif folder_for_name == 'rj_space_title_naming':
            folder_name = f'RJ{work_id:08d} {work_title}' if len(str(work_id)) > 6 else f'RJ{work_id:06d} {work_title}'
        elif folder_for_name == 'rj_underscore_title_naming':
            folder_name = f'RJ{work_id:08d}_{work_title}' if len(str(work_id)) > 6 else f'RJ{work_id:06d}_{work_title}'
        else:
            folder_name = work_title
            
        work_download_dir = os.path.join(download_dir, folder_name)
        
        try:
            if os.path.exists(work_download_dir):
                for file_info in self.work_detail['files']:
                    file_title = re.sub(r'[\/\\:\*\?\<\>\|]', '-', file_info['title'])

                    # 按照旧方法的逻辑进行文件类型筛选
                    file_type = file_title[file_title.rfind('.') + 1:].upper()
                    if not selected_formats.get(file_type, False):
                        continue  # 跳过不需要的文件类型
                    
                    # 获取文件夹路径并创建完整的文件路径
                    folder_path = file_info.get('folder_path', '')
                    if folder_path:
                        # 清理文件夹路径
                        clean_folder_path = re.sub(r'[<>:"|?*]', '_', folder_path)
                        clean_folder_path = clean_folder_path.rstrip('. ')
                        # 替换路径分隔符为本地格式
                        clean_folder_path = clean_folder_path.replace('/', os.sep)
                        
                        file_path = os.path.join(work_download_dir, clean_folder_path, file_title)
                    else:
                        file_path = os.path.join(work_download_dir, file_title)
                    
                    if os.path.exists(file_path):
                        # 使用os.path.getsize获取实际文件大小，支持大文件
                        actual_size = os.path.getsize(file_path)
                        expected_size = file_info.get('size', 0)
                        # 确保expected_size是数字类型，支持超大数值
                        if isinstance(expected_size, str):
                            try:
                                expected_size = int(expected_size)
                            except ValueError:
                                expected_size = 0
                        
                        # 取实际大小和期望大小的最小值，避免超过文件实际大小
                        downloaded_size += min(actual_size, expected_size)
        except Exception as e:
            print(f"计算已下载大小时出错: {e}")
            return 0
        
        return downloaded_size

    def format_bytes(self, bytes_value):
        """格式化字节数为可读格式，支持超大文件(>100GB)"""
        # 确保 bytes_value 是数字类型
        if isinstance(bytes_value, str):
            try:
                bytes_value = float(bytes_value)
            except ValueError:
                return "0 B"
        
        if bytes_value == 0:
            return "0 B"
        elif bytes_value >= 1024 * 1024 * 1024 * 1024:  # TB
            return f"{bytes_value / (1024 * 1024 * 1024 * 1024):.2f} TB"
        elif bytes_value >= 1024 * 1024 * 1024:  # GB
            return f"{bytes_value / (1024 * 1024 * 1024):.2f} GB"
        elif bytes_value >= 1024 * 1024:  # MB
            return f"{bytes_value / (1024 * 1024):.2f} MB"
        elif bytes_value >= 1024:  # KB
            return f"{bytes_value / 1024:.1f} KB"
        else:
            return f"{int(bytes_value)} B"

    def update_language(self):
        """更新语言显示"""
        # 更新状态标签
        if not self.is_downloading:
            if self.work_detail:
                self.status_label.setText(f"{language_manager.get_text('ready_to_download')} ({len(self.work_detail['files'])} {language_manager.get_text('files')})")
            else:
                self.status_label.setText(language_manager.get_text('waiting'))
        elif self.is_paused:
            self.status_label.setText(language_manager.get_text('paused'))
        else:
            self.status_label.setText(language_manager.get_text('downloading'))

        # 更新速度标签
        if self.download_speed >= 1024:
            self.speed_label.setText(f"{self.download_speed/1024:.1f} {language_manager.get_text('mb_per_second')}")
        else:
            self.speed_label.setText(f"{self.download_speed:.1f} {language_manager.get_text('kb_per_second')}")

        # 更新加载状态
        if not self.work_detail and self.size_label.text() == "Loading...":
            self.size_label.setText(language_manager.get_text('loading'))


class DownloadListThread(QThread):
    list_updated = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            print("开始获取下载列表...")
            works_list = get_down_list()
            
            # 检查是否返回了错误标识
            if isinstance(works_list, str):
                if works_list == "TOKEN_EXPIRED":
                    self.error_occurred.emit("TOKEN_EXPIRED")
                    return
                elif works_list == "NETWORK_ERROR":
                    self.error_occurred.emit("NETWORK_ERROR")
                    return
                elif works_list == "API_ERROR":
                    self.error_occurred.emit("API_ERROR")
                    return
                elif works_list == "JSON_PARSE_ERROR":
                    self.error_occurred.emit("JSON_PARSE_ERROR")
                    return
            
            # 检查是否是有效的列表数据
            if isinstance(works_list, list) and works_list:
                print(f"成功获取到 {len(works_list)} 个下载项目")
                self.list_updated.emit(works_list)
            else:
                error_msg = "API返回空列表或数据格式错误"
                print(f"错误: {error_msg}")
                self.error_occurred.emit("EMPTY_LIST")
        except Exception as e:
            error_msg = f"Failed to get download list: {str(e)}"
            print(f"异常错误: {error_msg}")
            print(f"异常类型: {type(e).__name__}")
            import traceback
            print(f"完整错误堆栈:")
            traceback.print_exc()
            self.error_occurred.emit(f"EXCEPTION: {str(e)}")


class DownloadPage(QWidget):
    def __init__(self):
        super().__init__()
        self.conf = ReadConf()
        self.download_items = {}
        self.download_manager = None
        self.is_downloading_active = False  # 跟踪是否有活动下载
        self.setup_ui()
        self.setup_download_manager()
        self.load_download_list()


    def setup_ui(self):
        self.setWindowTitle(language_manager.get_text('app_title'))
        self.setFixedSize(700, 500)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # 顶部控制栏
        top_layout = QHBoxLayout()

        # 标题
        # title_label = QLabel("ASMR_download")
        # title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        # top_layout.addWidget(title_label)

        # 语言选择
        language_label = QLabel("Language:")
        top_layout.addWidget(language_label)

        self.language_combo = QComboBox()
        self.language_combo.addItem("中文", "zh")
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("日本語", "ja")

        # 设置当前语言
        current_lang = language_manager.current_language
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == current_lang:
                self.language_combo.setCurrentIndex(i)
                break

        self.language_combo.currentIndexChanged.connect(self.on_language_changed)
        top_layout.addWidget(self.language_combo)

        top_layout.addStretch()

        # 全局速度显示
        self.global_speed_label = QLabel(f"{language_manager.get_text('total_speed')}: 0 {language_manager.get_text('kb_per_second')}")
        self.global_speed_label.setStyleSheet("color: #0066cc; font-weight: bold;")
        top_layout.addWidget(self.global_speed_label)

        # 开始/停止下载按钮
        self.start_all_button = QPushButton(language_manager.get_text('start_download'))
        self.start_all_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.start_all_button.clicked.connect(self.toggle_downloads)
        self.start_all_button.setEnabled(False)
        top_layout.addWidget(self.start_all_button)

        # 刷新按钮
        self.refresh_button = QPushButton(language_manager.get_text('refresh_list'))
        self.refresh_button.clicked.connect(self.load_download_list)
        top_layout.addWidget(self.refresh_button)

        # 设置按钮
        self.settings_button = QPushButton(language_manager.get_text('settings'))
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
        self.status_label = QLabel(language_manager.get_text('waiting'))
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.count_label = QLabel(f"{language_manager.get_text('total_count')}: 0")
        self.count_label.setStyleSheet("color: #666; font-size: 11px;")
        status_layout.addWidget(self.count_label)

        layout.addLayout(status_layout)

        self.setLayout(layout)

    def setup_download_manager(self):
        """设置下载管理器"""
        # 从配置文件获取下载路径，不再默认创建downloads文件夹
        download_conf = self.conf.read_download_conf()
        download_dir = download_conf['download_path']
        
        # 只在用户指定的下载路径不存在时才创建
        if not os.path.exists(download_dir):
            os.makedirs(download_dir, exist_ok=True)
            print(f"创建用户指定的下载目录: {download_dir}")
        
        self.download_manager = MultiFileDownloadManager(download_dir)

        # 连接下载管理器信号
        self.download_manager.download_started.connect(self.on_download_started)
        self.download_manager.download_progress.connect(self.on_download_progress)
        self.download_manager.download_completed.connect(self.on_download_completed)
        self.download_manager.download_failed.connect(self.on_download_failed)
        self.download_manager.speed_updated.connect(self.on_speed_updated)
        self.download_manager.file_filter_stats.connect(self.on_file_filter_stats)

        self.download_manager.start()

    def update_download_path(self):
        """动态更新下载路径，无需重启程序"""
        if self.download_manager:
            download_conf = self.conf.read_download_conf()
            new_download_dir = download_conf['download_path']
            self.download_manager.update_download_dir(new_download_dir)
            print(f"下载路径已更新为: {new_download_dir}")

    def load_download_list(self):
        self.status_label.setText(language_manager.get_text('loading'))
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

        self.count_label.setText(f"{language_manager.get_text('total_count')}: {len(works_list)}")
        self.status_label.setText(f"{language_manager.get_text('loaded_items')} {len(works_list)} {language_manager.get_text('download_items')}")

        # 如果有下载项，启用开始全部下载按钮
        if works_list:
            self.start_all_button.setEnabled(True)

    def on_list_error(self, error_msg):
        print(f"列表获取错误: {error_msg}")
        
        # 根据错误类型显示对应的多语言提示
        if error_msg == "TOKEN_EXPIRED":
            title = language_manager.get_text('token_expired')
            message = language_manager.get_text('token_expired')
            detail = language_manager.get_text('relogin_required')
        elif error_msg == "NETWORK_ERROR":
            title = language_manager.get_text('network_error') 
            message = language_manager.get_text('network_error')
            detail = "请检查:\n1. 网络连接是否正常\n2. 代理设置是否正确\n3. 防火墙是否阻止了连接"
        elif error_msg == "API_ERROR":
            title = language_manager.get_text('api_error')
            message = language_manager.get_text('api_error')
            detail = "请检查:\n1. API服务是否正常\n2. 尝试切换镜像站点\n3. 稍后重试"
        elif error_msg == "JSON_PARSE_ERROR":
            title = language_manager.get_text('json_parse_error')
            message = language_manager.get_text('json_parse_error')
            detail = "服务器返回了无效的数据格式，请尝试切换镜像站点或稍后重试"
        elif error_msg == "EMPTY_LIST":
            title = language_manager.get_text('empty_list')
            message = language_manager.get_text('empty_list')
            detail = "可能的原因:\n1. 您的下载列表为空\n2. 筛选条件过于严格\n3. 账号权限不足"
        else:
            # 处理其他异常错误
            title = language_manager.get_text('error')
            message = "获取下载列表失败"
            detail = f"详细错误信息:\n{error_msg}\n\n请检查:\n1. 网络连接是否正常\n2. 登录信息是否有效\n3. API服务是否可用\n4. 代理设置是否正确"
        
        # 更新状态标签
        self.status_label.setText(f"{language_manager.get_text('error')}: {title}")
        
        # 弹出相应的错误对话框
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle(language_manager.get_text('error'))
        msg_box.setText(message)
        msg_box.setDetailedText(detail)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        result = msg_box.exec()

        # 如果是TOKEN_EXPIRED错误，点击OK后跳转到设置页面
        if error_msg == "TOKEN_EXPIRED" and result == QMessageBox.StandardButton.Ok:
            self.open_settings()

    def add_download_item(self, work_info):
        item_widget = DownloadItemWidget(work_info, parent_page=self)
        item_widget.detail_ready.connect(self.check_start_all_button)

        # 插入到倒数第二个位置（最后一个是stretch）
        self.download_layout.insertWidget(self.download_layout.count() - 1, item_widget)

        self.download_items[str(work_info['id'])] = item_widget

    def collapse_all_except(self, exception_widget):
        """收起所有展开的项，除了指定的项"""
        for item in self.download_items.values():
            if item != exception_widget and item.is_expanded:
                item.collapse_tree()

    def clear_all_items(self):
        # 清空所有下载项
        for item_id in list(self.download_items.keys()):
            item = self.download_items[item_id]
            self.download_layout.removeWidget(item)
            item.deleteLater()
            del self.download_items[item_id]

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
            self.download_items[work_id].update_progress(100, 0, 0, language_manager.get_text('completed'))
        self.update_global_speed()

        # 调用review函数更新作品状态
        try:
            check_db = self.conf.check_DB()
            review(int(work_id), check_db)
            print(f"已更新作品 RJ{work_id} 的状态")
        except Exception as e:
            print(f"更新作品状态失败: {str(e)}")

        # 检查是否还有等待中的下载任务
        if self.download_manager and len(self.download_manager.download_queue) > 0:
            self.status_label.setText(f"{language_manager.get_text('download_completed')}: RJ{work_id}, {language_manager.get_text('continue_next')}")
        else:
            # 所有下载完成，重置按钮状态
            self.is_downloading_active = False
            self.start_all_button.setText(language_manager.get_text('start_download'))
            self.start_all_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            self.status_label.setText(language_manager.get_text('all_downloads_completed'))

    def on_download_failed(self, work_id, error):
        """下载失败"""
        if work_id in self.download_items:
            self.download_items[work_id].set_error(error)
        self.update_global_speed()
        
        # 下载失败时重置按钮状态
        self.is_downloading_active = False
        self.start_all_button.setText(language_manager.get_text('start_download'))
        self.start_all_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        # 显示错误对话框
        self.show_download_error(work_id, error)

    def on_speed_updated(self, work_id, speed_kbps):
        """速度更新"""
        if work_id in self.download_items:
            self.download_items[work_id].update_speed(speed_kbps)
        self.update_global_speed()

    def on_file_filter_stats(self, work_id, api_total, actual_total, skipped_total, total_files, skipped_files):
        """文件筛选统计信息"""
        def format_size(size):
            """格式化文件大小"""
            if size >= 1024**3:
                return f"{size / (1024**3):.2f} GB"
            elif size >= 1024**2:
                return f"{size / (1024**2):.2f} MB"
            elif size >= 1024:
                return f"{size / 1024:.2f} KB"
            else:
                return f"{size} B"

        # 更新状态标签显示统计信息
        status_text = f"作品 RJ{work_id}: "
        status_text += f"总文件 {total_files} 个, "
        if skipped_files > 0:
            status_text += f"跳过 {skipped_files} 个({format_size(skipped_total)}), "
        status_text += f"下载 {total_files - skipped_files} 个({format_size(actual_total)})"

        self.status_label.setText(status_text)

    def check_start_all_button(self):
        """检查是否应该启用开始全部下载按钮"""
        ready_count = 0
        for item in self.download_items.values():
            if item.work_detail and not item.is_downloading:
                ready_count += 1

        # 如果有准备好的下载项，启用按钮
        self.start_all_button.setEnabled(ready_count > 0)

    def toggle_downloads(self):
        """切换下载状态：开始下载或停止下载"""
        if not self.is_downloading_active:
            # 当前没有下载，开始下载
            self.start_downloads()
        else:
            # 当前有下载，停止下载
            self.stop_downloads()

    def start_downloads(self):
        """开始下载"""
        # 获取所有准备好的下载项，按添加顺序排列
        ready_items = []
        for i in range(self.download_layout.count() - 1):  # 排除最后的stretch
            widget = self.download_layout.itemAt(i).widget()
            if isinstance(widget, DownloadItemWidget):
                if (not widget.is_downloading and widget.work_detail):
                    ready_items.append(widget)

        if ready_items:
            # 开始第一个下载
            first_item = ready_items[0]
            work_id, work_detail = first_item.start_download()
            
            # 添加到下载管理器
            if self.download_manager and work_id and work_detail:
                # 找到对应的work_info
                first_item = ready_items[0]
                self.download_manager.add_download(int(work_id), work_detail, first_item.work_info)
                self.download_manager.start_next_download()

            # 将剩余的添加到队列
            for item in ready_items[1:]:
                if self.download_manager:
                    self.download_manager.add_download(int(item.work_info['id']), item.work_detail, item.work_info)

            # 更新状态
            self.is_downloading_active = True
            self.start_all_button.setText(language_manager.get_text('stop_download'))
            self.start_all_button.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
            self.status_label.setText(f"{language_manager.get_text('start_sequential_download')} {len(ready_items)} {language_manager.get_text('tasks')}")
        else:
            self.status_label.setText(language_manager.get_text('no_downloadable_tasks'))

    def stop_downloads(self):
        """停止所有下载"""
        # 停止下载管理器
        if self.download_manager:
            # 清空队列
            self.download_manager.download_queue.clear()
            
            # 取消所有活动下载
            for work_id in list(self.download_manager.active_downloads.keys()):
                self.download_manager.cancel_download(work_id)

        # 更新所有下载项状态
        for item in self.download_items.values():
            if item.is_downloading:
                item.is_downloading = False
                item.is_paused = False
                item.status_label.setText(language_manager.get_text('ready_to_download'))
                item.speed_label.setText("0 KB/s")

        # 更新按钮状态
        self.is_downloading_active = False
        self.start_all_button.setText(language_manager.get_text('start_download'))
        self.start_all_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.status_label.setText(language_manager.get_text('all_downloads_stopped'))


    def on_language_changed(self, index):
        """语言选择改变时的处理函数"""
        language_code = self.language_combo.itemData(index)
        if language_code:
            self.change_language(language_code)

    def change_language(self, language_code):
        """切换语言"""
        language_manager.set_language(language_code)
        self.update_ui_text()

    def update_ui_text(self):
        """更新界面文本"""
        # 更新窗口标题
        self.setWindowTitle(language_manager.get_text('app_title'))

        # 更新顶部按钮（根据当前状态显示相应文本）
        if self.is_downloading_active:
            self.start_all_button.setText(language_manager.get_text('stop_download'))
        else:
            self.start_all_button.setText(language_manager.get_text('start_download'))
        
        self.refresh_button.setText(language_manager.get_text('refresh_list'))
        self.settings_button.setText(language_manager.get_text('settings'))

        # 更新全局速度标签
        current_speed = self.global_speed_label.text().split(': ')[1] if ': ' in self.global_speed_label.text() else f"0 {language_manager.get_text('kb_per_second')}"
        self.global_speed_label.setText(f"{language_manager.get_text('total_speed')}: {current_speed}")

        # 更新底部状态
        current_count = self.count_label.text().split(': ')[1] if ': ' in self.count_label.text() else "0"
        self.count_label.setText(f"{language_manager.get_text('total_count')}: {current_count}")

        # 更新所有下载项目的语言显示
        for item in self.download_items.values():
            item.update_language()

    def open_settings(self):
        """打开设置页面"""
        from src.UI.set_config import SetConfig
        if not hasattr(self, 'settings_page') or not self.settings_page:
            self.settings_page = SetConfig()
            # 连接下载路径更改信号
            self.settings_page.download_path_changed.connect(self.update_download_path)
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
            self.global_speed_label.setText(f"{language_manager.get_text('total_speed')}: {total_speed/1024:.2f} {language_manager.get_text('mb_per_second')}")
        else:
            self.global_speed_label.setText(f"{language_manager.get_text('total_speed')}: {total_speed:.1f} {language_manager.get_text('kb_per_second')}")

    def show_download_error(self, work_id, error_msg):
        """显示下载错误对话框"""
        # 获取作品信息
        work_title = "未知作品"
        if work_id in self.download_items:
            work_title = self.download_items[work_id].work_info.get('title', '未知作品')
        
        # 创建错误对话框
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(language_manager.get_text('download_error'))
        msg_box.setText(f"{language_manager.get_text('download_failed')}")
        
        # 详细信息
        detail_text = f"作品: RJ{work_id} - {work_title}\n\n错误信息:\n{error_msg}\n\n下载队列已停止，请检查网络连接或稍后重试。"
        msg_box.setDetailedText(detail_text)
        
        # 设置按钮
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # 更新状态标签
        self.status_label.setText(f"{language_manager.get_text('error')}: RJ{work_id} {language_manager.get_text('download_failed')}")
        
        # 显示对话框
        msg_box.exec()
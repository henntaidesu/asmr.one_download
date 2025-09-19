import os
import time
import requests
from PyQt6.QtCore import QThread, pyqtSignal
from src.read_conf import ReadConf


class DownloadThread(QThread):
    progress_updated = pyqtSignal(int, 'PyQt_PyObject', 'PyQt_PyObject', str)  # progress%, downloaded_bytes, total_bytes, status
    download_finished = pyqtSignal(str)  # work_id
    download_error = pyqtSignal(str, str)  # work_id, error_message
    speed_updated = pyqtSignal(str, float)  # work_id, speed_kb_s
    file_filter_stats = pyqtSignal('PyQt_PyObject', 'PyQt_PyObject', 'PyQt_PyObject', int, int)  # api_total, actual_total, skipped_total, total_files, skipped_files

    def __init__(self, work_id, work_detail, download_dir):
        super().__init__()
        self.work_id = str(work_id)
        self.work_detail = work_detail
        self.download_dir = download_dir
        self.is_paused = False
        self.is_cancelled = False
        self.downloaded_bytes = 0
        self.total_bytes = work_detail.get('total_size', 0)
        self.start_time = time.time()
        self.last_update_time = time.time()
        self.last_downloaded = 0

        # 读取速度限制配置 (MB/s)
        conf = ReadConf()
        download_conf = conf.read_download_conf()
        self.speed_limit_mbps = download_conf['speed_limit']  # MB/s
        self.speed_limit_bps = self.speed_limit_mbps * 1024 * 1024  # 转换为 bytes/s

        # 令牌桶算法参数
        self.bucket_size = self.speed_limit_bps  # 桶大小等于每秒允许的字节数
        self.tokens = self.bucket_size  # 初始令牌数
        self.last_refill_time = time.time()

    def refill_tokens(self):
        """补充令牌桶中的令牌"""
        if self.speed_limit_bps <= 0:
            return

        current_time = time.time()
        elapsed = current_time - self.last_refill_time

        # 根据时间补充令牌
        tokens_to_add = elapsed * self.speed_limit_bps
        self.tokens = min(self.bucket_size, self.tokens + tokens_to_add)
        self.last_refill_time = current_time

    def consume_tokens(self, bytes_needed):
        """消费令牌，如果令牌不足则等待"""
        if self.speed_limit_bps <= 0:
            return

        self.refill_tokens()

        if self.tokens >= bytes_needed:
            self.tokens -= bytes_needed
        else:
            # 计算需要等待的时间
            deficit = bytes_needed - self.tokens
            wait_time = deficit / self.speed_limit_bps
            time.sleep(wait_time)

            # 重新补充令牌并消费
            self.refill_tokens()
            self.tokens = max(0, self.tokens - bytes_needed)

    def run(self):
        try:
            self.download_files()
        except Exception as e:
            self.download_error.emit(self.work_id, str(e))

    def download_files(self):
        conf = ReadConf()
        proxy = conf.read_proxy_conf()

        if proxy['open_proxy']:
            proxy_url = {
                'http': f'{proxy["proxy_type"]}://{proxy["host"]}:{proxy["port"]}',
                'https': f'{proxy["proxy_type"]}://{proxy["host"]}:{proxy["port"]}'
            }
        else:
            proxy_url = None

        # 读取文件类型配置
        conf = ReadConf()
        selected_formats = conf.read_downfile_type()

        # 重新计算实际要下载的文件总大小（排除跳过的文件）
        actual_total_size = 0
        skipped_total_size = 0
        total_downloaded = 0
        total_files = len(self.work_detail['files'])
        skipped_files = 0

        for file_info in self.work_detail['files']:
            # 按照旧方法的逻辑进行文件类型筛选
            file_title = file_info['title']
            file_type = file_title[file_title.rfind('.') + 1:].upper()

            # 获取文件大小
            file_size = file_info.get('size', 0)
            if isinstance(file_size, str):
                try:
                    file_size = int(file_size)
                except ValueError:
                    file_size = 0

            if not selected_formats.get(file_type, False):
                # 跳过的文件，累计跳过大小和数量
                skipped_total_size += file_size
                skipped_files += 1
                continue

            # 需要下载的文件，累计到实际总大小
            actual_total_size += file_size

            filename = self.sanitize_filename(file_info['title'])
            # 保持API返回的目录结构，但根目录使用配置的命名方式
            folder_path = file_info.get('folder_path', '')
            if folder_path:
                # 清理文件夹路径
                clean_folder_path = self.sanitize_folder_path(folder_path)
                # 创建子文件夹
                subfolder_dir = os.path.join(self.download_dir, clean_folder_path)
                file_path = os.path.join(subfolder_dir, filename)
            else:
                file_path = os.path.join(self.download_dir, filename)

            # 标准化路径
            file_path = os.path.normpath(file_path)

            if os.path.exists(file_path):
                # 使用os.path.getsize获取实际文件大小，支持大文件
                downloaded_size = os.path.getsize(file_path)
                # 确保不超过文件实际大小
                downloaded_size = min(downloaded_size, file_size)
                total_downloaded += downloaded_size

        # 发送文件筛选统计信息到UI
        api_total_size = self.work_detail.get('total_size', 0)
        self.file_filter_stats.emit(api_total_size, actual_total_size, skipped_total_size, total_files, skipped_files)
        
        # 不发送初始进度更新，避免覆盖界面已显示的正确大小

        for file_info in self.work_detail['files']:
            if self.is_cancelled:
                return

            # 按照旧方法的逻辑进行文件类型筛选
            file_title = file_info['title']
            file_type = file_title[file_title.rfind('.') + 1:].upper()
            if not selected_formats.get(file_type, False):
                print(f"跳过文件: {file_title}")
                continue

            file_size = file_info['size']
            download_url = file_info['download_url']
            filename = self.sanitize_filename(file_info['title'])
            
            # 保持API返回的目录结构，但根目录使用配置的命名方式
            folder_path = file_info.get('folder_path', '')
            if folder_path:
                # 清理文件夹路径，移除不合法字符
                clean_folder_path = self.sanitize_folder_path(folder_path)
                if clean_folder_path:  # 确保清理后的路径不为空
                    # 创建子文件夹
                    subfolder_dir = os.path.join(self.download_dir, clean_folder_path)
                    subfolder_dir = os.path.normpath(subfolder_dir)  # 标准化路径
                    os.makedirs(subfolder_dir, exist_ok=True)
                    file_path = os.path.join(subfolder_dir, filename)
                    file_path = os.path.normpath(file_path)  # 标准化路径
                    print(f"下载文件到子文件夹: {clean_folder_path}/{filename}")
                else:
                    file_path = os.path.join(self.download_dir, filename)
                    file_path = os.path.normpath(file_path)  # 标准化路径
                    print(f"文件夹路径无效，下载文件到根目录: {filename}")
            else:
                file_path = os.path.join(self.download_dir, filename)
                file_path = os.path.normpath(file_path)  # 标准化路径
                print(f"下载文件到根目录: {filename}")

            # 检查文件是否已存在并完整
            if os.path.exists(file_path):
                file_downloaded = os.path.getsize(file_path)
                if file_downloaded >= file_size:
                    print(f"文件已完整下载，跳过: {filename}")
                    continue
            else:
                file_downloaded = 0

            try:
                headers = {}
                if file_downloaded > 0:
                    headers['Range'] = f'bytes={file_downloaded}-'

                response = requests.get(download_url, headers=headers, stream=True, proxies=proxy_url)
                response.raise_for_status()
                
                with open(file_path, 'ab' if file_downloaded > 0 else 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if self.is_cancelled:
                            return

                        while self.is_paused and not self.is_cancelled:
                            time.sleep(0.1)

                        if chunk:
                            chunk_size = len(chunk)

                            # 使用令牌桶算法进行速度限制
                            self.consume_tokens(chunk_size)

                            f.write(chunk)
                            file_downloaded += chunk_size
                            total_downloaded += chunk_size

                            # 更新进度（使用实际下载的总大小），支持超大文件
                            progress = min(int((total_downloaded / actual_total_size) * 100), 100) if actual_total_size > 0 else 0
                            self.progress_updated.emit(progress, total_downloaded, actual_total_size, "下载中...")

                            # 计算并发送速度更新
                            current_time = time.time()
                            time_diff = current_time - self.last_update_time

                            if time_diff >= 0.5:  # 每0.5秒更新一次速度
                                bytes_diff = total_downloaded - self.last_downloaded
                                speed_bps = bytes_diff / time_diff
                                speed_kbps = speed_bps / 1024

                                self.speed_updated.emit(self.work_id, speed_kbps)
                                self.last_update_time = current_time
                                self.last_downloaded = total_downloaded

            except requests.exceptions.RequestException as e:
                self.download_error.emit(self.work_id, f"下载文件 {filename} 失败: {str(e)}")
                return
            except Exception as e:
                self.download_error.emit(self.work_id, f"保存文件 {filename} 失败: {str(e)}")
                return

        if not self.is_cancelled:
            # 使用实际下载的总大小
            self.progress_updated.emit(100, actual_total_size, actual_total_size, "下载完成")
            self.download_finished.emit(self.work_id)

    def pause_download(self):
        self.is_paused = True

    def resume_download(self):
        self.is_paused = False

    def cancel_download(self):
        self.is_cancelled = True
        self.quit()

    def sanitize_filename(self, filename):
        """清理文件名，移除不合法字符"""
        import re
        # 移除或替换Windows不允许的字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 移除末尾的点和空格
        filename = filename.rstrip('. ')
        # 限制文件名长度
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        return filename or "unnamed_file"

    def sanitize_folder_path(self, folder_path):
        """清理文件夹路径，保留路径分隔符但移除不合法字符"""
        import re
        if not folder_path:
            return ""
        
        # 分割路径为各个部分
        path_parts = folder_path.split('/')
        cleaned_parts = []
        
        for part in path_parts:
            if part:  # 跳过空字符串
                # 清理每个文件夹名称，但不移除路径分隔符
                cleaned_part = re.sub(r'[<>:"|?*]', '_', part)  # 不包含 / 和 \
                cleaned_part = cleaned_part.rstrip('. ')
                # 限制文件夹名长度
                if len(cleaned_part) > 100:
                    cleaned_part = cleaned_part[:100]
                if cleaned_part:
                    cleaned_parts.append(cleaned_part)
        
        # 使用系统相应的路径分隔符连接路径
        return os.sep.join(cleaned_parts) if cleaned_parts else ""


class MultiFileDownloadManager(QThread):
    """管理多个作品的下载"""
    download_started = pyqtSignal(str)  # work_id
    download_progress = pyqtSignal(str, int, 'PyQt_PyObject', 'PyQt_PyObject', str)  # work_id, progress%, downloaded, total, status
    download_completed = pyqtSignal(str)  # work_id
    download_failed = pyqtSignal(str, str)  # work_id, error
    speed_updated = pyqtSignal(str, float)  # work_id, speed
    file_filter_stats = pyqtSignal(str, 'PyQt_PyObject', 'PyQt_PyObject', 'PyQt_PyObject', int, int)  # work_id, api_total, actual_total, skipped_total, total_files, skipped_files

    def __init__(self, download_dir):
        super().__init__()
        self.download_dir = download_dir
        self.download_queue = []
        self.active_downloads = {}
        self.max_concurrent = 1  # 顺序下载，一次只下载一个

    def add_download(self, work_id, work_detail, work_info=None):
        """添加下载任务到队列"""
        self.download_queue.append((work_id, work_detail, work_info))

    def get_folder_name(self, work_id, work_detail, work_info=None):
        """根据配置获取文件夹名称，与旧方法保持一致"""
        import re
        conf = ReadConf()
        folder_for_name = conf.read_name()

        # 优先使用work_info（与旧方法一致），否则使用work_detail
        if work_info:
            work_title = re.sub(r'[\/\\:\*\?\<\>\|]', '-', work_info['title'])
            work_id = work_info['id']
        else:
            work_title = re.sub(r'[\/\\:\*\?\<\>\|]', '-', work_detail.get('title', f'Work_{work_id}'))
            work_id = int(work_id)

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

        return folder_name

    def start_next_download(self):
        """开始下一个下载任务"""
        if len(self.active_downloads) >= self.max_concurrent or not self.download_queue:
            return

        # 处理新的参数格式
        queue_item = self.download_queue.pop(0)
        if len(queue_item) == 3:
            work_id, work_detail, work_info = queue_item
        else:
            work_id, work_detail = queue_item
            work_info = None

        # 根据配置的文件夹命名方式创建作品目录
        folder_name = self.get_folder_name(work_id, work_detail, work_info)
        print(f"生成的文件夹名: '{folder_name}'")
        work_dir = os.path.join(self.download_dir, folder_name)
        print(f"完整路径: '{work_dir}'")

        # 标准化路径并创建目录
        work_dir = os.path.normpath(work_dir)
        print(f"标准化后路径: '{work_dir}'")
        os.makedirs(work_dir, exist_ok=True)

        download_thread = DownloadThread(work_id, work_detail, work_dir)
        download_thread.progress_updated.connect(
            lambda p, d, t, s, wid=work_id: self.download_progress.emit(str(wid), p, d, t, s)
        )
        download_thread.download_finished.connect(self.on_download_finished)
        download_thread.download_error.connect(self.on_download_error)
        download_thread.speed_updated.connect(self.speed_updated.emit)
        download_thread.file_filter_stats.connect(
            lambda api, actual, skipped, total_f, skipped_f, wid=work_id: self.file_filter_stats.emit(str(wid), api, actual, skipped, total_f, skipped_f)
        )

        self.active_downloads[str(work_id)] = download_thread
        download_thread.start()
        self.download_started.emit(str(work_id))

    def on_download_finished(self, work_id):
        """下载完成处理"""
        if work_id in self.active_downloads:
            thread = self.active_downloads[work_id]
            thread.quit()
            thread.wait()
            del self.active_downloads[work_id]

        self.download_completed.emit(work_id)
        self.start_next_download()  # 开始下一个下载

    def on_download_error(self, work_id, error):
        """下载错误处理"""
        if work_id in self.active_downloads:
            thread = self.active_downloads[work_id]
            thread.quit()
            thread.wait()
            del self.active_downloads[work_id]

        # 清空下载队列，停止后续下载
        self.download_queue.clear()
        
        self.download_failed.emit(work_id, error)
        # 不再自动开始下一个下载，让用户决定是否继续

    def pause_download(self, work_id):
        """暂停指定下载"""
        if work_id in self.active_downloads:
            self.active_downloads[work_id].pause_download()

    def resume_download(self, work_id):
        """继续指定下载"""
        if work_id in self.active_downloads:
            self.active_downloads[work_id].resume_download()

    def cancel_download(self, work_id):
        """取消指定下载"""
        if work_id in self.active_downloads:
            thread = self.active_downloads[work_id]
            thread.cancel_download()
            thread.wait()
            del self.active_downloads[work_id]

    def run(self):
        """启动下载管理器"""
        while len(self.active_downloads) < self.max_concurrent and self.download_queue:
            self.start_next_download()
            time.sleep(0.1)
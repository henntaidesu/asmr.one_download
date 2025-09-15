import os
import time
import requests
from PyQt6.QtCore import QThread, pyqtSignal
from src.read_conf import ReadConf


class DownloadThread(QThread):
    progress_updated = pyqtSignal(int, int, int, str)  # progress%, downloaded_bytes, total_bytes, status
    download_finished = pyqtSignal(str)  # work_id
    download_error = pyqtSignal(str, str)  # work_id, error_message
    speed_updated = pyqtSignal(str, float)  # work_id, speed_kb_s

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

        # 直接使用API返回的总大小，始终不变
        total_size = self.work_detail.get('total_size', 0)
        
        # 计算已下载的总大小（包括已存在的文件）
        total_downloaded = 0
        for file_info in self.work_detail['files']:
            filename = self.sanitize_filename(file_info['title'])
            file_path = os.path.join(self.download_dir, filename)
            if os.path.exists(file_path):
                downloaded_size = os.path.getsize(file_path)
                # 确保不超过文件实际大小
                downloaded_size = min(downloaded_size, file_info['size'])
                total_downloaded += downloaded_size

        print(f"开始下载: 总大小 {total_size} bytes, 已下载 {total_downloaded} bytes")
        
        # 不发送初始进度更新，避免覆盖界面已显示的正确大小
        
        for file_info in self.work_detail['files']:
            if self.is_cancelled:
                return

            file_size = file_info['size']
            download_url = file_info['download_url']
            filename = self.sanitize_filename(file_info['title'])
            file_path = os.path.join(self.download_dir, filename)

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

                            # 更新进度（使用API返回的总大小）
                            progress = int((total_downloaded / total_size) * 100) if total_size > 0 else 0
                            self.progress_updated.emit(progress, total_downloaded, total_size, "下载中...")

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
            # 使用API返回的总大小
            self.progress_updated.emit(100, total_size, total_size, "下载完成")
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


class MultiFileDownloadManager(QThread):
    """管理多个作品的下载"""
    download_started = pyqtSignal(str)  # work_id
    download_progress = pyqtSignal(str, int, int, int, str)  # work_id, progress%, downloaded, total, status
    download_completed = pyqtSignal(str)  # work_id
    download_failed = pyqtSignal(str, str)  # work_id, error
    speed_updated = pyqtSignal(str, float)  # work_id, speed

    def __init__(self, download_dir):
        super().__init__()
        self.download_dir = download_dir
        self.download_queue = []
        self.active_downloads = {}
        self.max_concurrent = 1  # 顺序下载，一次只下载一个

    def add_download(self, work_id, work_detail):
        """添加下载任务到队列"""
        self.download_queue.append((work_id, work_detail))

    def start_next_download(self):
        """开始下一个下载任务"""
        if len(self.active_downloads) >= self.max_concurrent or not self.download_queue:
            return

        work_id, work_detail = self.download_queue.pop(0)

        # 创建作品目录
        work_dir = os.path.join(self.download_dir, f"RJ{int(work_id):06d}")
        os.makedirs(work_dir, exist_ok=True)

        download_thread = DownloadThread(work_id, work_detail, work_dir)
        download_thread.progress_updated.connect(
            lambda p, d, t, s, wid=work_id: self.download_progress.emit(str(wid), p, d, t, s)
        )
        download_thread.download_finished.connect(self.on_download_finished)
        download_thread.download_error.connect(self.on_download_error)
        download_thread.speed_updated.connect(self.speed_updated.emit)

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

        self.download_failed.emit(work_id, error)
        self.start_next_download()  # 开始下一个下载

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
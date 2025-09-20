"""
下载相关线程类模块
包含工作详情获取线程和下载列表获取线程
"""

from PyQt6.QtCore import QThread, pyqtSignal
from src.asmr_api.get_down_list import get_down_list
from src.download.download_utils import get_work_detail_sync


class WorkDetailThread(QThread):
    """工作详情获取线程"""
    detail_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, work_id):
        super().__init__()
        self.work_id = work_id

    def run(self):
        try:
            detail = get_work_detail_sync(self.work_id)
            if detail:
                self.detail_loaded.emit(detail)
            else:
                self.error_occurred.emit("Failed to get work detail")
        except Exception as e:
            self.error_occurred.emit(str(e))


class DownloadListThread(QThread):
    """下载列表获取线程"""
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
            if isinstance(works_list, list):
                if works_list:
                    print(f"成功获取到 {len(works_list)} 个下载项目")
                else:
                    print("API返回的works列表为空，但这是有效的响应")
                self.list_updated.emit(works_list)
            else:
                error_msg = "API返回数据格式错误"
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

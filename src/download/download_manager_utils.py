"""
下载管理器业务逻辑模块
包含下载管理相关的业务逻辑函数
"""

import os
from src.read_conf import ReadConf
from src.download.download_thread import MultiFileDownloadManager
from src.download.download_utils import update_work_review_status


def setup_download_manager():
    """设置下载管理器"""
    conf = ReadConf()
    # 从配置文件获取下载路径，不再默认创建downloads文件夹
    download_conf = conf.read_download_conf()
    download_dir = download_conf['download_path']
    
    # 只在用户指定的下载路径不存在时才创建
    if not os.path.exists(download_dir):
        os.makedirs(download_dir, exist_ok=True)
        print(f"创建用户指定的下载目录: {download_dir}")
    
    return MultiFileDownloadManager(download_dir)


def update_download_path_if_needed(download_manager):
    """动态更新下载路径，无需重启程序"""
    if download_manager:
        conf = ReadConf()
        download_conf = conf.read_download_conf()
        new_download_dir = download_conf['download_path']
        download_manager.update_download_dir(new_download_dir)
        print(f"下载路径已更新为: {new_download_dir}")


def process_download_completion(work_id):
    """处理下载完成后的操作"""
    print(f"下载完成: {work_id}")
    
    # 调用review函数更新作品状态
    update_work_review_status(work_id)
    
    return True


def get_ready_download_items(download_layout, item_class):
    """获取所有准备好的下载项，按添加顺序排列"""
    ready_items = []
    for i in range(download_layout.count() - 1):  # 排除最后的stretch
        widget = download_layout.itemAt(i).widget()
        if isinstance(widget, item_class):
            if (not widget.is_downloading and widget.work_detail):
                ready_items.append(widget)
    return ready_items


def start_first_download_and_queue_others(ready_items, download_manager):
    """开始第一个下载并将其他项添加到队列"""
    if not ready_items or not download_manager:
        return False
    
    # 开始第一个下载
    first_item = ready_items[0]
    work_id, work_detail = first_item.start_download()
    
    # 添加到下载管理器
    if work_id and work_detail:
        download_manager.add_download(int(work_id), work_detail, first_item.work_info)
        download_manager.start_next_download()

    # 将剩余的添加到队列
    for item in ready_items[1:]:
        download_manager.add_download(int(item.work_info['id']), item.work_detail, item.work_info)
    
    return True


def stop_all_downloads(download_manager, download_items):
    """停止所有下载"""
    # 停止下载管理器
    if download_manager:
        # 清空队列
        download_manager.download_queue.clear()
        
        # 取消所有活动下载
        for work_id in list(download_manager.active_downloads.keys()):
            download_manager.cancel_download(work_id)

    # 更新所有下载项状态
    for item in download_items.values():
        if item.is_downloading:
            item.is_downloading = False
            item.is_paused = False
            # 状态更新将在UI层处理
    
    return True


def check_download_queue_status(download_manager):
    """检查下载队列状态"""
    if download_manager and len(download_manager.download_queue) > 0:
        return "has_queue"
    else:
        return "queue_empty"


def clear_download_items_from_layout(download_layout, download_items):
    """从布局中清空所有下载项"""
    # 清空所有下载项widget
    for item_id in list(download_items.keys()):
        item = download_items[item_id]
        download_layout.removeWidget(item)
        item.deleteLater()
        del download_items[item_id]
    
    return True


def handle_error_types(error_msg):
    """处理不同类型的错误并返回相应的错误信息"""
    error_mappings = {
        "TOKEN_EXPIRED": {
            "title": "token_expired",
            "message": "token_expired", 
            "detail": "relogin_required"
        },
        "NETWORK_ERROR": {
            "title": "network_error",
            "message": "network_error",
            "detail": "请检查:\n1. 网络连接是否正常\n2. 代理设置是否正确\n3. 防火墙是否阻止了连接"
        },
        "API_ERROR": {
            "title": "api_error",
            "message": "api_error", 
            "detail": "请检查:\n1. API服务是否正常\n2. 尝试切换镜像站点\n3. 稍后重试"
        },
        "JSON_PARSE_ERROR": {
            "title": "json_parse_error",
            "message": "json_parse_error",
            "detail": "服务器返回了无效的数据格式，请尝试切换镜像站点或稍后重试"
        },
        "EMPTY_LIST": {
            "title": "empty_list",
            "message": "empty_list",
            "detail": "可能的原因:\n1. 您的下载列表为空\n2. 筛选条件过于严格\n3. 账号权限不足"
        }
    }
    
    if error_msg in error_mappings:
        return error_mappings[error_msg]
    else:
        # 处理其他异常错误
        return {
            "title": "error",
            "message": "获取下载列表失败",
            "detail": f"详细错误信息:\n{error_msg}\n\n请检查:\n1. 网络连接是否正常\n2. 登录信息是否有效\n3. API服务是否可用\n4. 代理设置是否正确"
        }

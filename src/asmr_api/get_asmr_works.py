import re
import os
import time
import requests
from tqdm import tqdm
from src.read_conf import ReadConf


def down_file(url, file_name, stop_event):
    """
    下载文件，支持断点续传、速度限制、线程停止。
    """
    conf = ReadConf()
    download_conf_data = conf.read_download_conf()
    speed_limit = download_conf_data["speed_limit"]
    max_retries = download_conf_data["max_retries"]
    timeout = download_conf_data["timeout"]

    try:
        # 获取文件总大小
        response = requests.head(url, timeout=timeout)
        if response.status_code != 200:
            print(f"无法获取文件信息，状态码: {response.status_code}")
            return False

        total_size = int(response.headers.get("Content-Length", 0))

        # 检查本地文件是否已存在且完整
        if os.path.exists(file_name):
            downloaded_size = os.path.getsize(file_name)
            if downloaded_size == total_size:
                print(f"文件已完整下载，跳过下载: {file_name}")
                return True
        else:
            downloaded_size = 0

        # 设置请求头，支持断点续传
        headers = {"Range": f"bytes={downloaded_size}-"}

        retries = 0
        while retries < max_retries:
            try:
                with requests.get(url, headers=headers, stream=True, timeout=timeout) as resp, \
                        open(file_name, "ab") as file, \
                        tqdm(
                            desc="下载中",
                            total=total_size,
                            initial=downloaded_size,
                            unit="B",
                            unit_scale=True,
                            unit_divisor=1024,
                        ) as bar:
                    start_time = time.time()
                    bytes_downloaded_in_second = 0

                    for chunk in resp.iter_content(chunk_size=1024):
                        if stop_event.is_set():
                            print("检测到停止信号，终止下载")
                            return False
                        if chunk:
                            file.write(chunk)
                            bar.update(len(chunk))
                            bytes_downloaded_in_second += len(chunk)

                            # 限制下载速度
                            elapsed_time = time.time() - start_time
                            if elapsed_time < 1 and bytes_downloaded_in_second >= speed_limit * 1024 * 1024:
                                time.sleep(1 - elapsed_time)
                                start_time = time.time()
                                bytes_downloaded_in_second = 0

                return True

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                retries += 1
                print(f"下载超时或连接错误，正在重试 ({retries}/{max_retries})...")
                time.sleep(2)

        print("下载失败，已达到最大重试次数。")
        return False

    except Exception as e:
        print(f"下载出错: {e}")
        return False


def collect_audio_info(node, base_path, parent_folder=None):
    """
    递归收集当前节点及其子节点的音频信息。
    """
    results = []
    node_type = node.get("type")
    node_title = node.get("title")

    if node_type == "folder":
        # 如果是文件夹类型，递归收集子节点
        children = node.get("children", [])
        for child in children:
            new_base_path = os.path.join(base_path, node_title) if node_title else base_path
            results.extend(collect_audio_info(child, new_base_path, node_title))
    else:
        # 如果是文件，提取音频信息
        media_url = node.get("mediaStreamUrl") or node.get("mediaDownloadUrl")
        results.append({
            "file_type": node_type,
            "folder_title": parent_folder,
            "title": node_title,
            "media_download_url": media_url,
            "download_path": base_path
        })

    return results


def parse_req(req, rj_number, download_path):
    """
    从请求数据中解析所有文件信息。
    """
    all_results = []
    base_path = os.path.join(download_path, rj_number)

    for item in req:
        all_results.extend(collect_audio_info(item, base_path))

    return all_results


def get_asmr_downlist_api(stop_event):
    """
    主下载逻辑，支持线程停止。
    """
    from src.asmr_api.get_down_list import get_down_list
    from src.asmr_api.works_review import review
    from src.datebase_execution import MySQLDB

    works_list = get_down_list()
    conf = ReadConf()
    folder_flag = conf.read_name()
    selected_formats = conf.read_downfile_type()
    check_DB = conf.check_DB()

    if not works_list:
        print("未获取到作品列表")
        return

    for work in works_list:
        if stop_event.is_set():
            print("检测到停止信号，终止下载")
            return

        download_conf_data = conf.read_download_conf()
        download_path = download_conf_data["download_path"]
        keyword = work["id"]
        work_title = re.sub(r'[\/\\:\*\?\<\>\|]', '-', work["title"])

        # 根据配置调整文件夹命名方式
        if folder_flag == 'RJ号命名':
            work_title = f'RJ{keyword:06d}'

        try:
            # 检查是否开启数据库
            if check_DB:
                rj_number = f'RJ{keyword:06d}'
                sql = f"SELECT work_state FROM `works` WHERE work_id = '{rj_number}'"
                DB_flag = int(MySQLDB().select(sql)[1][0][0])
                if DB_flag < 0:
                    print(f"作品已下载: {rj_number}")
                    review(keyword, check_DB)
                    continue
        except Exception as e:
            print(f"数据库检查出错: {e}")

        url = f"https://api.asmr-200.com/api/tracks/{keyword}?v=1"
        req = requests.get(url).json()

        # 解析下载信息
        results = parse_req(req, work_title, download_path)
        for idx, item in enumerate(results, start=1):
            if stop_event.is_set():
                print("检测到停止信号，终止下载")
                return

            file_title = item['title']
            file_type = file_title[file_title.rfind('.') + 1:].upper()
            if not selected_formats.get(file_type, False):
                print(f"跳过不支持的文件类型: {file_title}")
                continue

            print(f"正在下载作品 {work_title} ({idx}/{len(results)})")
            file_name = os.path.join(item["download_path"], item["title"])

            if not os.path.exists(item["download_path"]):
                os.makedirs(item["download_path"], exist_ok=True)

            success = down_file(item['media_download_url'], file_name, stop_event)
            if not success:
                print(f"下载失败: {file_title}")

        # 更新数据库状态
        if check_DB:
            sql = f"UPDATE `works` SET `work_state` = '-1' WHERE `work_id` = '{rj_number}';"
            MySQLDB().update(sql)

        review(keyword, check_DB)

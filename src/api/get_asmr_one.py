import time
import requests
import re
from tqdm import tqdm
import os
from src.module.read_conf import ReadConf

speed_limit, download_path = ReadConf().get_download_conf()


def down_file(url, file_name, download_speed_limit=7 * 1024 * 1024):
    try:
        # 获取文件总大小
        response = requests.head(url)
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

        # 执行下载
        with requests.get(url, headers=headers, stream=True) as resp, \
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
                if chunk:
                    file.write(chunk)
                    bar.update(len(chunk))
                    bytes_downloaded_in_second += len(chunk)

                    # 限制下载速度
                    elapsed_time = time.time() - start_time
                    if elapsed_time < 1 and bytes_downloaded_in_second >= download_speed_limit:
                        time.sleep(1 - elapsed_time)
                        start_time = time.time()
                        bytes_downloaded_in_second = 0

        print(f"\n文件已成功下载并保存为: {file_name}")
        return True

    except Exception as e:
        print(f"下载出错: {e}")
        return False


def collect_audio_info(node, base_path, parent_folder=None):
    """
    递归收集当前节点及其子节点的音频信息:
    node          : 当前节点(可能是文件或文件夹)
    base_path     : 下载根目录(逐层拼接文件夹名称)
    parent_folder : 当前节点的上层文件夹名称
    """
    results = []
    node_type = node.get("type")
    node_title = node.get("title")

    # 如果是文件夹类型，遍历其子节点并递归收集
    if node_type == "folder":
        children = node.get("children", [])
        for child in children:
            # 子节点的 base_path 需要在原有基础上拼上当前 folder 的名称
            new_base_path = os.path.join(base_path, node_title) if node_title else base_path
            results.extend(collect_audio_info(child, new_base_path, node_title))
    else:
        # 如果是文件(非 folder)，提取下载链接
        # 有时是 mediaStreamUrl，有时是 mediaDownloadUrl
        media_url = node.get("mediaStreamUrl") or node.get("mediaDownloadUrl")
        audio_info = {
            "file_type": node_type,
            "folder_title": parent_folder,
            "title": node_title,
            "media_download_url": media_url,
            "download_path": base_path
        }
        results.append(audio_info)

    return results


def parse_req(req, rj_number):
    """
    从 req 中解析出所有文件信息并返回
    """
    all_results = []
    base_path = os.path.join(download_path, rj_number)

    for item in req:
        all_results.extend(collect_audio_info(item, base_path))

    return all_results


def get_asmr_downlist_api(rj_number):
    url = f"https://api.asmr-200.com/api/tracks/{re.search(r"\d+", rj_number).group()}?v=1"
    req = requests.get(url).json()

    # 收集所有文件下载信息
    results = parse_req(req, rj_number)

    # 执行下载
    for idx, item in enumerate(results, start=1):
        print(f'正在下载第 ({idx} / {len(results)}) 个文件')
        print(f"文件类型： {item['file_type']}")
        print(f"文件标题: {item['title']}")
        print(f"下载链接: {item['media_download_url']}")
        print(f"下载路径: {item['download_path']}")
        print("-" * 40)

        folder_path = item["download_path"]
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)

        file_name = os.path.join(folder_path, item["title"])
        down_file(item['media_download_url'], file_name)
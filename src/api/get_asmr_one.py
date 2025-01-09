import time
import requests
import re
from tqdm import tqdm
import os
from src.module.read_conf import ReadConf

speed_limit, download_path = ReadConf().get_download_conf()

def get_asmr_downlist_api(rj_number):
    url = f"https://api.asmr-200.com/api/tracks/{re.search(r"\d+", rj_number).group()}?v=1"
    req = requests.get(url).json()

    results = []
    for folder in req:
        folder_title = folder["title"]
        for child in folder["children"]:
            audio_info = {
                "folder_type": folder_title,
                "title": child["title"],
                "work_id": child["work"]["id"],
                "source_id": child["work"]["source_id"],
                "media_download_url": child["mediaDownloadUrl"],
                # "duration": child["duration"],
                "size": child["size"],
            }
            results.append(audio_info)
    down_flag = 1
    for item in results:
        print(f'正在下载第 ({down_flag} / {len(results)}) 个文件')
        print(f"文件夹类型: {item['folder_type']}")
        print(f"文件标题: {item['title']}")
        print(f"工作 ID: {item['work_id']}")
        print(f"来源 ID: {item['source_id']}")
        print(f"下载链接: {item['media_download_url']}")
        # print(f"时长: {item['duration']} 秒")
        print(f"文件大小: {item['size']} 字节")
        print("-" * 40)
        os.makedirs(f"{download_path}/{rj_number}/{item['folder_type']}", exist_ok=True)
        time.sleep(1)
        down_file(item['media_download_url'], f"{download_path}/{rj_number}/{item['folder_type']}/{item['title']}")
        down_flag += 1

def down_file(url, file_name):
    download_speed_limit = 7 * 1024 * 1024  # 5 MB/s

    try:
        # 获取文件总大小
        response = requests.head(url)
        if response.status_code != 200:
            print(f"无法获取文件信息，状态码: {response.status_code}")
            exit(1)

        total_size = int(response.headers.get("Content-Length", 0))

        # 检查本地文件是否已存在
        if os.path.exists(file_name):
            downloaded_size = os.path.getsize(file_name)
            if downloaded_size == total_size:
                print(f"文件已完整下载，跳过下载: {file_name}")
                return True
        else:
            downloaded_size = 0

        # 设置请求头，支持断点续传
        headers = {"Range": f"bytes={downloaded_size}-"}

        # 开始下载
        with requests.get(url, headers=headers, stream=True) as response, open(file_name, "ab") as file, tqdm(
                desc="下载中",
                total=total_size,
                initial=downloaded_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
        ) as bar:
            # 记录每秒钟开始的时间和累计下载的字节数
            start_time = time.time()
            bytes_downloaded_in_second = 0

            for chunk in response.iter_content(chunk_size=1024):
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
    except Exception as e:
        print(f"下载出错: {e}")
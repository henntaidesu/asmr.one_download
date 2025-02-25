import re
import os
import time
import requests
from tqdm import tqdm
# from src.UI.index import INDEX
from src.read_conf import ReadConf
from http.client import IncompleteRead

def down_file(url, file_name, stop_event):
    """
    下载文件，支持断点续传、速度限制、线程停止。
    """
    conf = ReadConf()
    download_conf_data = conf.read_download_conf()
    speed_limit = download_conf_data["speed_limit"]
    max_retries = download_conf_data["max_retries"]
    timeout = download_conf_data["timeout"]
    min_speed = download_conf_data["min_speed"] * 1024
    speed_check_interval = download_conf_data["min_speed_check"]
    proxy = conf.read_proxy_conf()
    if proxy['open_proxy']:
        proxy_url = {
            f'http': f'{proxy["proxy_type"]}://{proxy["host"]}:{proxy["port"]}',
            f'https': f'{proxy["proxy_type"]}://{proxy["host"]}:{proxy["port"]}'
        }
    else:
        proxy_url = None
    try:
        retries = 1
        while retries < max_retries:
            try:
                # 获取文件总大小
                response = requests.head(url, timeout=timeout)
                if response.status_code != 200:
                    return False, f"无法获取文件信息，状态码: {response.status_code}"

                total_size = int(response.headers.get("Content-Length", 0))

                # 检查本地文件是否已存在且完整
                if os.path.exists(file_name):
                    downloaded_size = os.path.getsize(file_name)
                    if downloaded_size == total_size:
                        print(f"文件已下载，跳过下载: {file_name}")
                        return True, 'INFO'
                else:
                    downloaded_size = 0

                # 设置请求头，支持断点续传
                headers = {"Range": f"bytes={downloaded_size}-"}

                with requests.get(url, headers=headers, stream=True, timeout=timeout, proxies=proxy_url) as resp, \
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
                    last_check_time = start_time
                    bytes_downloaded_since_last_check = 0

                    for chunk in resp.iter_content(chunk_size=1024):
                        # time.sleep(0.5)
                        if stop_event.is_set():
                            print("检测到停止信号，终止下载")
                            return False, 'INFO'
                        if chunk:
                            file.write(chunk)
                            bar.update(len(chunk))
                            bytes_downloaded_since_last_check += len(chunk)
                            # 限制下载速度
                            elapsed_time = time.time() - start_time
                            if elapsed_time < 1 and bytes_downloaded_since_last_check >= speed_limit * 1024 * 1024:
                                time.sleep(1 - elapsed_time)
                                start_time = time.time()
                                bytes_downloaded_since_last_check = 0

                            # 每30秒检查一次下载速度
                            current_time = time.time()
                            if current_time - last_check_time >= speed_check_interval:
                                current_speed = bytes_downloaded_since_last_check / (current_time - last_check_time)
                                if current_speed < min_speed:
                                    print(f"下载速度低于{min_speed}KB/s ({current_speed / 1024:.2f} KB/s 正在重试 ({retries}/{max_retries})，重启下载...")
                                    retries += 1
                                    break

                                last_check_time = current_time
                                bytes_downloaded_since_last_check = 0

                    else:
                        return True, '下载完成'

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                retries += 1
                print(f"下载超时或连接错误，正在重试 ({retries}/{max_retries})...")
                time.sleep(2)

            except IncompleteRead as e:
                retries += 1
                print(f"连接中断，数据不完整，正在重试 ({retries}/{max_retries})...")
                try:
                    # 删除不完整的文件
                    if os.path.exists(file_name):
                        os.remove(file_name)
                        print("已删除不完整的文件")
                except Exception as err:
                    print(f"删除文件失败: {err}")
                time.sleep(2)

            except Exception as e:
                if type(e).__name__ == 'ChunkedEncodingError':
                    print(f'文件校验出错，正在重试 ({retries}/{max_retries})...')
                    retries += 1
                    print(file_name)
                    if retries > max_retries - 2:
                        return False, f'{file_name},文件校验错误，建议前往网页点击一下对应项目加载，加载出后返回程序重新下载'
                    try:
                        # 确保文件关闭后再删除
                        if os.path.exists(file_name):
                            os.remove(file_name)
                            print("文件已删除")
                    except Exception as err:
                        print(f"删除文件失败: {err}")
                    time.sleep(2)

        print("下载失败，已达到最大重试次数。")
        return False, '下载失败，已达到最大重试次数。'

    except Exception as e:
        print(f"下载出错: {e}")
        print(type(e).__name__)
        return False, e


def collect_audio_info(node, base_path, parent_folder=None):
    """
    递归收集当前节点及其子节点的音频信息。
    """
    results = []
    node_type = node.get("type")
    node_title = node.get("title")
    try:
        if node_type == "folder":
            # 如果是文件夹类型，递归收集子节点
            children = node.get("children", [])
            for child in children:
                new_base_path = os.path.join(base_path, node_title) if node_title else base_path
                results.extend(collect_audio_info(child, new_base_path, node_title))
        else:
            # 如果是文件，提取音频信息
            media_url = node.get("mediaStreamUrl") or node.get("mediaDownloadUrl")
            # if parent_folder:
            #     parent_folder = parent_folder.re.sub(r'[\/\\:\*\?\<\>\|]', '-', parent_folder)
            results.append({
                "file_type": node_type,
                "folder_title": parent_folder,
                "title": node_title,
                "media_download_url": media_url,
                "download_path": base_path
            })

        return results
    except Exception as e:
        print(e)


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

    conf = ReadConf()
    folder_flag = conf.read_name()
    selected_formats = conf.read_downfile_type()
    check_DB = conf.check_DB()

    while True:
        works_list = get_down_list()
        if not works_list:
            print("未获取到作品列表 休眠24小时")
            time.sleep(3600 * 24)
            continue
            # return False, "未获取到作品列表"
        for work in works_list:
            if stop_event.is_set():
                print("检测到停止信号，终止下载")
                return False, "用户停止下载"

            download_conf_data = conf.read_download_conf()
            download_path = download_conf_data["download_path"]
            keyword = work["id"]
            work_title = re.sub(r'[\/\\:\*\?\<\>\|]', '-', work["title"])

            # 根据配置调整文件夹命名方式
            if folder_flag == 'RJ号命名':
                if len(str(keyword)) > 6:
                    work_title = f'RJ{keyword:08d}'
                else:
                    work_title = f'RJ{keyword:06d}'

            elif folder_flag == 'RJ号 标题命名':
                if len(str(keyword)) > 6:
                    work_title = f'RJ{keyword:08d} {work_title}'
                else:
                    work_title = f'RJ{keyword:06d} {work_title}'

            elif folder_flag == 'RJ号_标题命名':
                if len(str(keyword)) > 6:
                    work_title = f'RJ{keyword:08d}_{work_title}'
                else:
                    work_title = f'RJ{keyword:06d}_{work_title}'

            try:
                # 检查是否开启数据库
                if check_DB:
                    if len(str(keyword)) > 6:
                        rj_number = f'RJ{keyword:08d}'
                    else:
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
                    return True, "用户停止下载"

                file_title = item['title']
                file_title = re.sub(r'[\/\\:\*\?\<\>\|]', '-', file_title)
                file_type = file_title[file_title.rfind('.') + 1:].upper()
                if not selected_formats.get(file_type, False):
                    print(f"跳过文件: {file_title}")
                    continue

                print(f"-" * 80)
                print(f"正在下载： {work_title} ({idx}/{len(results)})")
                print(f"文件类型： {item['file_type']}")
                print(f"文件名称： {item['title']}")

                file_name = os.path.join(item["download_path"], file_title)

                if not os.path.exists(item["download_path"]):
                    os.makedirs(item["download_path"], exist_ok=True)

                success, message = down_file(item['media_download_url'], file_name, stop_event)
                if not success:
                    print(f"下载失败: {file_title} \n {message}")
                    return success, message

                time.sleep(0.5)

            # 更新数据库状态
            if check_DB:
                sql = f"UPDATE `works` SET `work_state` = '-1' WHERE `work_id` = '{rj_number}';"
                MySQLDB().update(sql)

            review(keyword, check_DB)

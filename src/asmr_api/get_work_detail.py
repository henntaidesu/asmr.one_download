import requests
from src.read_conf import ReadConf


def get_work_detail(work_id):
    """
    获取作品详细信息，包括文件列表和下载链接

    Args:
        work_id (int): 作品ID

    Returns:
        dict: 包含作品详细信息的字典，如果失败返回None
    """
    conf = ReadConf()

    website_course = conf.read_website_course()
    if website_course == 'Original':
        web_site = 'asmr.one'
    elif website_course == 'Mirror-1':
        web_site = 'asmr-100.com'
    elif website_course == 'Mirror-2':
        web_site = 'asmr-200.com'
    elif website_course == 'Mirror-3':
        web_site = 'asmr-300.com'

    url = f'https://api.{web_site}/api/tracks/{work_id}?v=1'

    user_data = conf.read_asmr_user()
    token = user_data['token']
    headers = {
        'authorization': f'Bearer {token}'
    }

    proxy = conf.read_proxy_conf()
    if proxy['open_proxy']:
        proxy_url = {
            'http': f'{proxy["proxy_type"]}://{proxy["host"]}:{proxy["port"]}',
            'https': f'{proxy["proxy_type"]}://{proxy["host"]}:{proxy["port"]}'
        }
    else:
        proxy_url = None

    try:
        response = requests.get(url, headers=headers, proxies=proxy_url)
        response.raise_for_status()
        tracks_data = response.json()

        # API返回的是数组格式
        if not tracks_data or not isinstance(tracks_data, list):
            return None

        # 从第一个track获取作品基本信息
        first_track = tracks_data[0] if tracks_data else {}
        work_info = first_track.get('work', {})

        work_detail = {
            'id': work_info.get('id', work_id),
            'title': first_track.get('workTitle', ''),
            'circle': '',  # API中没有circle信息
            'dl_count': 0,  # API中没有dl_count信息
            'total_size': 0,
            'files': []
        }

        # 处理所有文件
        for track in tracks_data:
            if track.get('mediaDownloadUrl'):
                file_info = {
                    'title': track.get('title', ''),
                    'download_url': track.get('mediaDownloadUrl'),
                    'size': track.get('size', 0),
                    'duration': track.get('duration', 0) if track.get('type') == 'audio' else 0,
                    'hash': track.get('hash', ''),
                    'type': track.get('type', 'other')
                }
                work_detail['files'].append(file_info)
                work_detail['total_size'] += file_info['size']

        return work_detail

    except requests.exceptions.RequestException as e:
        print(f"网络请求失败：{str(e)}")
        return None
    except Exception as e:
        print(f"获取作品详细信息时发生错误：{str(e)}")
        return None
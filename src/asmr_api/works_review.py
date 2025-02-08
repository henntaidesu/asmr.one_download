import requests
from src.read_conf import ReadConf


def review(work_id, check_DB):
    conf = ReadConf()
    url = f'https://api.asmr-200.com/api/review'

    user_data = conf.read_asmr_user()
    token = user_data['token']
    headers = {
        'authorization': f'Bearer {token}'
    }
    if check_DB:
        data = {
            'progress': 'listened',
            'work_id': work_id,
        }
    else:
        data = {
            'progress': 'listening',
            'work_id': work_id,
        }

    proxy = conf.read_proxy_conf()
    if proxy['open_proxy']:
        proxy_url = {
            f'http': f'{proxy["proxy_type"]}://{proxy["host"]}:{proxy["port"]}',
            f'https': f'{proxy["proxy_type"]}://{proxy["host"]}:{proxy["port"]}'
        }
    else:
        proxy_url = None

    requests.put(url, headers=headers, data=data, proxies=proxy_url)

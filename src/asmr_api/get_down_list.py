import requests
from src.read_conf import ReadConf


def get_down_list():
    conf = ReadConf()
    check_DB = conf.check_DB()

    website_course = conf.read_website_course()
    if website_course == 'Original':
        web_site = f'asmr.one'
    elif website_course == 'Mirror-1':
        web_site = 'asmr-100.com'
    elif website_course == 'Mirror-2':
        web_site = 'asmr-200.com'
    elif website_course == 'Mirror-3':
        web_site = 'asmr-300.com'

    if check_DB:
        url = f'https://api.{web_site}/api/review?order=updated_at&sort=desc&page=1&filter=listening'
    else:
        url = f'https://api.{web_site}/api/review?order=updated_at&sort=desc&page=1&filter=marked'

    user_data = conf.read_asmr_user()
    token = user_data['token']
    headers = {
        'authorization': f'Bearer {token}'
    }

    proxy = conf.read_proxy_conf()
    if proxy['open_proxy']:
        proxy_url = {
            f'http': f'{proxy["proxy_type"]}://{proxy["host"]}:{proxy["port"]}',
            f'https': f'{proxy["proxy_type"]}://{proxy["host"]}:{proxy["port"]}'
        }
    else:
        proxy_url = None

    req = requests.get(url, headers=headers, proxies=proxy_url).json()
    id_list = []

    if req['works']:
        data = req['works']
        for work in data:
            work_info = {
                'id': work['id'],
                'title': work['title'],
            }
            id_list.append(work_info)

    return id_list
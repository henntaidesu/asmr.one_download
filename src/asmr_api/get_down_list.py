import requests
from src.read_conf import ReadConf


def get_down_list():
    conf = ReadConf()
    check_DB = conf.check_DB()
    if check_DB:
        url = f'https://api.asmr-200.com/api/review?order=updated_at&sort=desc&page=1&filter=listening'
    else:
        url = f'https://api.asmr-200.com/api/review?order=updated_at&sort=desc&page=1&filter=marked'

    user_data = conf.read_asmr_user()
    token = user_data['token']
    headers = {
        'authorization': f'Bearer {token}'
    }
    req = requests.get(url, headers=headers).json()
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
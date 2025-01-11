import requests
from src.read_conf import ReadConf


def review(work_id):
    url = f'https://api.asmr-200.com/api/review'

    conf = ReadConf()
    user_data = conf.read_asmr_user()
    token = user_data['token']
    headers = {
        'authorization': f'Bearer {token}'
    }
    data = {
        'progress': 'listening',
        'work_id': work_id,
    }

    requests.put(url, headers=headers, data=data)

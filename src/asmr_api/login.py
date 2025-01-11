import requests
from src.read_conf import ReadConf



def login():
    conf = ReadConf()
    data = conf.read_asmr_user()
    username = data['username']
    passwd = data['passwd']
    url = 'https://api.asmr-200.com/api/auth/me'
    data = {
        'name': username,
        'password': passwd,
    }
    req = requests.post(url, data=data).json()

    try:
        if req['user']['loggedIn']:
            conf.write_asmr_token(req['user']['recommenderUuid'], req['token'])
            return True
    except KeyError:
        return req['error']


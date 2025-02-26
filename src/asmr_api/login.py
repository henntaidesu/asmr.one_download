import requests
from src.read_conf import ReadConf



def login():
    conf = ReadConf()
    data = conf.read_asmr_user()
    username = data['username']
    passwd = data['passwd']

    website_course = conf.read_website_course()
    if website_course == 'Original':
        web_site = f'asmr.one'
    elif website_course == 'Mirror-1':
        web_site = 'asmr-100.com'
    elif website_course == 'Mirror-2':
        web_site = 'asmr-200.com'
    elif website_course == 'Mirror-3':
        web_site = 'asmr-300.com'

    url = f'https://api.{web_site}/api/auth/me'
    data = {
        'name': username,
        'password': passwd,
    }

    proxy = conf.read_proxy_conf()
    if proxy['open_proxy']:
        proxy_url = {
            f'http': f'{proxy["proxy_type"]}://{proxy["host"]}:{proxy["port"]}',
            f'https': f'{proxy["proxy_type"]}://{proxy["host"]}:{proxy["port"]}'
        }
    else:
        proxy_url = None

    req = requests.post(url, data=data, proxies=proxy_url).json()

    try:
        if req['user']['loggedIn']:
            conf.write_asmr_token(req['user']['recommenderUuid'], req['token'])
            return True
    except KeyError:
        return req['error']


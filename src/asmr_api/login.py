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

    try:
        req = requests.post(url, data=data, proxies=proxy_url).json()

        # 检查响应是否包含用户信息
        if 'user' in req and req['user']['loggedIn']:
            conf.write_asmr_token(req['user']['recommenderUuid'], req['token'])
            return True

        # 检查是否有错误信息
        if 'error' in req:
            return req['error']

        # 如果响应结构不符合预期
        return f"登录失败：响应格式异常 - {str(req)}"

    except requests.exceptions.RequestException as e:
        return f"网络请求失败：{str(e)}"
    except Exception as e:
        return f"登录过程中发生错误：{str(e)}"


import sys
import time

import requests
import json
from src.module.execution_db import DB
from src.module.log import Log


def get_new_proxy():
    while True:
        url = f"http://zltiqu.pyhttp.taolop.com/getip?count=1&neek=104794&type=2&yys=0&port=1&sb=&mr=1&sep=0&ts=1&ys=1&cs=1&pack=41879"
        proxy_data = requests.get(url).text
        proxy_data = json.loads(proxy_data)
        if proxy_data['code'] == 0:
            for item in proxy_data['data']:
                IP = item['ip']
                Port = item['port']
                expire_time = item['expire_time']
                city = item['city']
                isp = item['isp']
                sql = (f"INSERT INTO `Movie`.`proxy_pool`"
                       f" (`address`, `port`, `status`, `proxy_type`, `expire_time`, `city`, `isp`) VALUES "
                       f"('{IP}', {Port}, '1', 'http', '{expire_time}', '{city}', '{isp}');")
                DB().insert(sql)
                Log().write_log(f"更新代理成功 ip - {IP}", 'I')
                time.sleep(3)
                return [f"http://{IP}:{Port}", expire_time]

        elif proxy_data['code'] == 111:
            time.sleep(3)
            continue

        else:
            Log().write_log(f"{proxy_data['code']} - {proxy_data['msg']}", 'error')
            sys.exit()


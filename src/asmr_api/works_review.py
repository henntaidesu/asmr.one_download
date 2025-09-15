import requests
import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from src.read_conf import ReadConf


def review(work_id, check_DB):
    """
    更新作品的收听状态
    
    Args:
        work_id (int): 作品ID
        check_DB (bool): 是否标记为已听完（True）或正在收听（False）
    
    Returns:
        bool: 是否更新成功
    """
    try:
        print(f"更新作品 {work_id} 状态: {'已听完' if check_DB else '正在收听'}")
        
        conf = ReadConf()

        website_course = conf.read_website_course()
        if website_course == 'Original':
            web_site = f'asmr.one'
        elif website_course == 'Mirror-1':
            web_site = 'asmr-100.com'
        elif website_course == 'Mirror-2':
            web_site = 'asmr-200.com'
        elif website_course == 'Mirror-3':
            web_site = 'asmr-300.com'
        url = f'https://api.{web_site}/api/review'

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

        response = requests.put(url, headers=headers, data=data, proxies=proxy_url, timeout=30)
        response.raise_for_status()
        print(f"成功更新作品 {work_id} 状态")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"网络请求失败: {str(e)}")
        return False
    except Exception as e:
        print(f"更新作品状态时发生错误: {str(e)}")
        return False

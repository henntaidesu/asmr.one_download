import os
import configparser
import pymysql

class ReadConf:
    config = None

    def __init__(self):
        if not os.path.exists('conf.ini'):
            create_ini_file()
        # 如果配置信息尚未加载，则加载配置文件
        if not ReadConf.config:
            ReadConf.config = self._load_config()

    def _load_config(self):
        self.config = configparser.ConfigParser()
        self.config.read('conf.ini', encoding='utf-8')
        return self.config

    def check_DB(self):
        open_DB = self.config.get('database', 'open_DB')
        if open_DB == 'True':
            return True
        else:
            return False

    def read_database(self):
        host = self.config.get('database', 'host')
        port = self.config.get('database', 'port')
        port = int(port)
        user = self.config.get('database', 'user')
        password = self.config.get('database', 'password')
        data_base = self.config.get('database', 'database')
        open_DB = self.config.get('database', 'open_DB')

        if open_DB == 'True':
            db = pymysql.connect(host=host, port=port, user=user, password=password, database=data_base)
            return db


    def read_downfile_type(self):
        file_types = ['MP3', 'MP4', 'FLAC', 'WAV', 'JPG', 'PNG', 'PDF', 'TXT', 'VTT', 'LRC']
        # 定义用于存储文件类型状态的字典
        file_type_status = {}
        # 将配置项值转换为布尔值的方法
        def to_bool(value):
            return value.lower() == 'true'
        # 遍历文件类型列表并读取配置
        for file_type in file_types:
            config_value = self.config.get('file_type', file_type, fallback='false')  # 添加 fallback，防止配置缺失报错
            file_type_status[file_type] = to_bool(config_value)
        return file_type_status

    def write_downfile_type(self, item_type, flag):
        self.config.set('file_type', item_type, flag)
        with open('conf.ini', 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def read_name(self):
        folder_for_name = self.config.get('name', 'name')
        return folder_for_name

    def write_folder_for_name(self, name):
        self.config.set('name', 'name', name)
        with open('conf.ini', 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def read_download_conf(self):
        speed_limit = float(self.config.get('down_conf', 'speed_limit'))
        download_path = self.config.get('down_conf', 'download_path')
        max_retries = int(self.config.get('down_conf', 'max_retries'))
        timeout = int(self.config.get('down_conf', 'timeout'))
        min_speed = int(self.config.get('down_conf', 'min_speed'))
        min_speed_check = int(self.config.get('down_conf', 'min_speed_check'))
        if download_path[1:] == '\\' or download_path[1:] == '/':
            download_path = download_path[:-1]
        if '\\' in download_path:
            download_path = download_path.replace('\\', '/')
        return {
            'speed_limit': speed_limit,
            'download_path': download_path,
            'max_retries': max_retries,
            'timeout': timeout,
            'min_speed': min_speed,
            'min_speed_check': min_speed_check,
        }

    def write_speed_limit(self, speed_limit):
        self.config.set('down_conf', 'speed_limit', speed_limit)
        with open('conf.ini', 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def write_max_retries(self, max_retries):
        self.config.set('down_conf', 'max_retries', max_retries)
        with open('conf.ini', 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def write_timeout(self, timeout):
        self.config.set('down_conf', 'timeout', timeout)
        with open('conf.ini', 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)


    def write_download_conf_(self, download_path):
        self.config.set('down_conf', 'download_path', download_path)
        with open('conf.ini', 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)


    def read_asmr_user(self):
        username = self.config.get('user', 'username')
        passwd = self.config.get('user', 'passwd')
        recommenderUuid = self.config.get('user', 'recommenderUuid')
        token = self.config.get('user', 'token')

        return {
            'username': username,
            'passwd': passwd,
            'recommenderUuid': recommenderUuid,
            'token': token
        }

    def write_asmr_username(self, username, passwd):
        self.config.set('user', 'username', username)
        self.config.set('user', 'passwd', passwd)
        with open('conf.ini', 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def write_asmr_token(self, recommenderUuid, token):
        self.config.set('user', 'recommenderUuid', recommenderUuid)
        self.config.set('user', 'token', token)
        with open('conf.ini', 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)


    def write_download_conf(self, speed_limit, download_path):
        self.config.set('down_conf', 'speed_limit', speed_limit)
        self.config.set('down_conf', 'download_path', download_path)
        with open('conf.ini', 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def read_proxy_conf(self):
        host = self.config.get('proxy', 'host')
        port = self.config.get('proxy', 'port')
        proxy_type = self.config.get('proxy', 'type')
        open_proxy = self.config.get('proxy', 'open_proxy')
        if open_proxy == 'True':
            open_proxy = True
        else:
            open_proxy = False
        return {
            'open_proxy': open_proxy,
            'host': host,
            'port': port,
            'proxy_type': proxy_type
        }

    def write_proxy_host(self, proxy_host):
        self.config.set('proxy', 'host', proxy_host)
        with open('conf.ini', 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def write_proxy_port(self, proxy_port):
        self.config.set('proxy', 'port', proxy_port)
        with open('conf.ini', 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def write_proxy_type(self, proxy_type):
        self.config.set('proxy', 'type', proxy_type)
        with open('conf.ini', 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def write_open_proxy(self, open_proxy):
        # if open_proxy:
        #     open_proxy = 'True'
        # else:
        #     open_proxy = 'False'
        self.config.set('proxy', 'open_proxy', open_proxy)
        with open('conf.ini', 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def read_website_course(self):
        site_source = self.config.get('mirror_site', 'site_source')
        return site_source

    def write_website_course(self, site_source):
        self.config.set('mirror_site', 'site_source', site_source)
        with open('conf.ini', 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def read_language_setting(self):
        """读取语言设置"""
        try:
            language_code = self.config.get('language', 'current')
            return language_code
        except (configparser.NoSectionError, configparser.NoOptionError):
            return 'zh'  # 默认中文

    def write_language_setting(self, language_code):
        """写入语言设置"""
        if not self.config.has_section('language'):
            self.config.add_section('language')
        self.config.set('language', 'current', language_code)
        with open('conf.ini', 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

def create_ini_file():
    config = configparser.ConfigParser()

    # 配置 [down_conf] 部分
    config['down_conf'] = {
        'speed_limit': '10',
        'max_retries': '10',
        'timeout': '10',
        'download_path': f'C:/Users/{os.getlogin()}/Downloads',
        'min_speed': '256',
        'min_speed_check': '30',
    }

    # 配置 [user] 部分
    config['user'] = {
        'username': '',
        'passwd': '',
        'recommenderUuid': '',
        'token': ''
    }

    # 配置文件夹命名方式
    config['name'] = {
        'name': '标题命名',
    }

    config['file_type'] = {
        'MP3': 'true',
        'MP4': 'true',
        'FLAC': 'true',
        'WAV': 'true',
        'JPG': 'true',
        'PNG': 'true',
        'PDF': 'true',
        'TXT': 'true',
        'VTT': 'true',
        'LRC': 'true',
    }

    config['database'] = {
        'host': 'localhost',
        'port': '3306',
        'user': 'root',
        'password': 'password',
        'database': 'asmr',
        'open_db': 'False'
    }

    config['proxy'] = {
        'open_proxy': 'False',
        'host': 'localhost',
        'port': '10809',
        'type': 'http',
    }

    config['mirror_site'] = {
        'site_source': 'Original',
    }

    # 配置语言设置
    config['language'] = {
        'current': 'zh',  # 默认中文
    }

    # 将配置写入文件
    with open('conf.ini', 'w', encoding='utf-8') as configfile:
        config.write(configfile)
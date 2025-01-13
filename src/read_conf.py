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

    def write_name(self, name):
        self.config.set('name', 'name', name)
        with open('conf.ini', 'w', encoding='utf-8') as configfile:
            self.config.write(configfile)

    def read_download_conf(self):
        speed_limit = float(self.config.get('down_conf', 'speed_limit'))
        download_path = self.config.get('down_conf', 'download_path')
        max_retries = int(self.config.get('down_conf', 'max_retries'))
        timeout = int(self.config.get('down_conf', 'timeout'))
        if download_path[1:] == '\\' or download_path[1:] == '/':
            download_path = download_path[:-1]
        if '\\' in download_path:
            download_path = download_path.replace('\\', '/')
        return {
            'speed_limit': speed_limit,
            'download_path': download_path,
            'max_retries': max_retries,
            'timeout': timeout,
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


def create_ini_file():
    config = configparser.ConfigParser()

    # 配置 [down_conf] 部分
    config['down_conf'] = {
        'speed_limit': '10',
        'max_retries': '10',
        'timeout': '10',
        'download_path': f'C:/Users/{os.getlogin()}/Downloads',
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

    # 将配置写入文件
    with open('conf.ini', 'w', encoding='utf-8') as configfile:
        config.write(configfile)
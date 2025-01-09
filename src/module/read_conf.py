import pymysql
import configparser


class ReadConf:
    config = None

    def __init__(self):
        # 如果配置信息尚未加载，则加载配置文件
        if not ReadConf.config:
            ReadConf.config = self._load_config()

    def _load_config(self):
        self.config = configparser.ConfigParser()
        self.config.read('conf.ini', encoding='utf-8')
        return self.config

    def database(self):
        host = self.config.get('database', 'host')
        port = int(self.config.get('database', 'port'))
        user = self.config.get('database', 'user')
        password = self.config.get('database', 'password')
        database = self.config.get('database', 'database')
        db = pymysql.connect(host=host, port=port, user=user, password=password, database=database)
        return db

    def log_level(self):
        level = self.config.get('LogLevel', 'level')
        return level

    def proxy_pool(self):
        proxy = self.config.get('proxy', 'proxy')
        if proxy == 'True':
            return True
        else:
            return False

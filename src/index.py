from src.module.read_conf import ReadConf
from src.api.get_asmr_one import get_asmr_downlist_api

class Index:

    def __init__(self):
        self.conf = ReadConf()

    @staticmethod
    def index():
        rj_number = input('输入下载RJ号 ： ')
        get_asmr_downlist_api(rj_number)
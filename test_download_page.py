#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试下载页面 - 仅显示真实下载状态
"""

import sys
from PyQt6.QtWidgets import QApplication
from src.UI.download_page import DownloadPage

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # 创建下载页面
    download_page = DownloadPage()
    download_page.show()

    sys.exit(app.exec())
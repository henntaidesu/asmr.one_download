#!/usr/bin/env python3
"""
测试下载功能集成
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from src.UI.download_page import DownloadPage

def test_download_page():
    """测试下载页面功能"""
    app = QApplication(sys.argv)

    # 创建下载页面
    download_page = DownloadPage()
    download_page.show()

    print("下载页面已启动，具有以下功能：")
    print("1. 自动获取下载列表")
    print("2. 为每个作品获取详细信息（文件大小、下载链接等）")
    print("3. 点击'开始'按钮开始下载")
    print("4. 实时显示下载速度和进度")
    print("5. 支持暂停、继续、取消下载")
    print("6. 显示全局下载速度")

    sys.exit(app.exec())

if __name__ == "__main__":
    test_download_page()
#!/usr/bin/env python3
"""
下载功能使用示例
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.asmr_api.get_work_detail import get_work_detail

def test_api_functionality():
    """测试API功能"""
    print("测试获取作品详细信息...")

    # 测试获取作品详细信息
    work_id = 1205338  # 示例作品ID
    work_detail = get_work_detail(work_id)

    if work_detail:
        print(f"作品标题: {work_detail['title']}")
        print(f"社团: {work_detail['circle']}")
        print(f"文件总数: {len(work_detail['files'])}")
        print(f"总大小: {work_detail['total_size'] / (1024*1024):.1f} MB")

        print("\n文件列表:")
        for i, file_info in enumerate(work_detail['files'][:3]):  # 只显示前3个文件
            print(f"  {i+1}. {file_info['title']}")
            print(f"     大小: {file_info['size'] / (1024*1024):.1f} MB")
            print(f"     类型: {file_info['type']}")
            print()
    else:
        print("获取作品详细信息失败")

if __name__ == "__main__":
    test_api_functionality()
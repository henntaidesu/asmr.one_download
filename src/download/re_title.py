"""
标题和文件名字符转换模块
提供Windows文件系统非法字符的转换功能
"""

import os


def sanitize_windows_filename(filename):
    """
    将Windows文件系统不支持的字符转换为相似的合法字符

    Args:
        filename: 原始文件名或标题

    Returns:
        转换后的合法文件名

    Windows不支持的字符映射:
        < -> 全角小于号
        > -> 全角大于号
        : -> 全角冒号
        " -> 中文双引号
        / -> 全角斜杠
        \\ -> 全角反斜杠
        | -> 全角竖线
        ? -> 全角问号
        * -> 全角星号
    """
    # 字符映射表：Windows不支持字符 -> 相似的合法字符
    char_map = {
        '<': '\uff1c',   # 全角小于号
        '>': '\uff1e',   # 全角大于号
        ':': '\uff1a',   # 全角冒号
        '"': '\u201c',   # 中文双引号
        '/': '\uff0f',   # 全角斜杠
        '\\': '\uff3c',  # 全角反斜杠
        '|': '\uff5c',   # 全角竖线
        '?': '\uff1f',   # 全角问号
        '*': '\uff0a'    # 全角星号
    }

    # 逐个替换字符
    for old_char, new_char in char_map.items():
        filename = filename.replace(old_char, new_char)

    # 移除末尾的点和空格（Windows不允许）
    filename = filename.rstrip('. ')

    return filename or "unnamed_file"


def sanitize_folder_path(folder_path):
    """
    清理文件夹路径，保留路径分隔符但将不合法字符转换为相似字符

    Args:
        folder_path: 原始文件夹路径（使用/分隔）

    Returns:
        清理后的文件夹路径（使用系统路径分隔符）
    """
    if not folder_path:
        return ""

    # 字符映射表（路径处理时不转换 / 和 \\，因为它们用作分隔符）
    char_map = {
        '<': '\uff1c',   # 全角小于号
        '>': '\uff1e',   # 全角大于号
        ':': '\uff1a',   # 全角冒号
        '"': '\u201c',   # 中文双引号
        '|': '\uff5c',   # 全角竖线
        '?': '\uff1f',   # 全角问号
        '*': '\uff0a'    # 全角星号
    }

    # 分割路径为各个部分
    path_parts = folder_path.split('/')
    cleaned_parts = []

    for part in path_parts:
        if part:  # 跳过空字符串
            cleaned_part = part
            # 替换不合法字符
            for old_char, new_char in char_map.items():
                cleaned_part = cleaned_part.replace(old_char, new_char)

            cleaned_part = cleaned_part.rstrip('. ')
            # 限制文件夹名长度
            if len(cleaned_part) > 100:
                cleaned_part = cleaned_part[:100]
            if cleaned_part:
                cleaned_parts.append(cleaned_part)

    # 使用系统相应的路径分隔符连接路径
    return os.sep.join(cleaned_parts) if cleaned_parts else ""

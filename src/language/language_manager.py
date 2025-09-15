#!/usr/bin/env python3
"""
多语言管理器
"""

import json
import os

class LanguageManager:
    def __init__(self):
        self.current_language = 'zh'  # 默认中文
        self.languages = {}
        self.load_languages()

    def load_languages(self):
        """加载所有语言文件"""
        language_dir = os.path.dirname(__file__)

        # 支持的语言
        supported_languages = ['zh', 'en', 'ja']

        for lang in supported_languages:
            lang_file = os.path.join(language_dir, f'{lang}.json')
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.languages[lang] = json.load(f)
            except FileNotFoundError:
                print(f"Language file {lang_file} not found")
                self.languages[lang] = {}

    def set_language(self, language_code):
        """设置当前语言"""
        if language_code in self.languages:
            self.current_language = language_code

    def get_text(self, key, default=None):
        """获取当前语言的文本"""
        if default is None:
            default = key

        current_lang_data = self.languages.get(self.current_language, {})
        return current_lang_data.get(key, default)

    def get_available_languages(self):
        """获取可用语言列表"""
        return {
            'zh': '中文',
            'en': 'English',
            'ja': '日本語'
        }

# 全局语言管理器实例
language_manager = LanguageManager()
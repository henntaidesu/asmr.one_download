#!/usr/bin/env python3
"""
多语言管理器
"""

import os
import configparser

# 静态导入语言模块，确保PyInstaller能正确打包
from src.language import zh, en, ja

class LanguageManager:
    def __init__(self):
        self.config_file = 'conf.ini'
        self.current_language = 'zh'  # 默认中文
        self.languages = {}
        self.load_language_config()
        self.load_languages()

    def load_languages(self):
        """加载所有语言文件"""
        # 使用静态导入的语言模块，确保PyInstaller能正确打包
        language_modules = {
            'zh': zh,
            'en': en,
            'ja': ja
        }

        for lang_code, lang_module in language_modules.items():
            try:
                self.languages[lang_code] = lang_module.TRANSLATIONS
                print(f"Loaded language module: {lang_code}")
            except AttributeError as e:
                print(f"Language module {lang_code} missing TRANSLATIONS: {e}")
                self.languages[lang_code] = {}

    def load_language_config(self):
        """从配置文件加载语言设置"""
        if os.path.exists(self.config_file):
            config = configparser.ConfigParser()
            try:
                config.read(self.config_file, encoding='utf-8')
                if 'language' in config and 'current' in config['language']:
                    self.current_language = config['language']['current']
            except Exception as e:
                print(f"Error loading language config: {e}")

    def save_language_config(self):
        """保存语言设置到配置文件"""
        config = configparser.ConfigParser()

        # 如果配置文件存在，先读取现有内容
        if os.path.exists(self.config_file):
            try:
                config.read(self.config_file, encoding='utf-8')
            except Exception as e:
                print(f"Error reading config file: {e}")

        # 设置语言配置
        if 'language' not in config:
            config.add_section('language')
        config['language']['current'] = self.current_language

        # 保存到文件
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config.write(f)
        except Exception as e:
            print(f"Error saving language config: {e}")

    def set_language(self, language_code):
        """设置当前语言"""
        if language_code in self.languages:
            self.current_language = language_code
            self.save_language_config()

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
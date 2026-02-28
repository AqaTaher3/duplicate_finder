# config.py
import json
import os
from pathlib import Path


class AppConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance._init_config()
        return cls._instance

    def _init_config(self):
        """مقداردهی اولیه تنظیمات"""
        self.config_file = "duplicates_cleaner_config.json"

        # تنظیمات پیش‌فرض
        self.settings = {
            # مسیرها
            "ffmpeg_path": r"D:\000_projects\librareis\ffmpeg\bin\ffmpeg.exe",
            "default_log_dir": "logs",

            # تنظیمات برنامه
            "app_name": "FileCleaner",
            "language": "fa",

            # تنظیمات عملکرد
            "max_workers": 4,
            "cache_enabled": True,
            "batch_size": 1000,
            "use_recycle_bin": True,

            # تنظیمات فیلترها
            "finding_corrupted_files": False,
            "min_similarity": 0.7,
            "min_name_length": 10,
            "same_extension_only": True,

            # فرمت‌های پشتیبانی شده
            "supported_extensions": [
                ".mp3", ".flac", ".wav", ".aac", ".ogg", ".m4a", ".wma",
                ".mp4", ".avi", ".mkv", ".mov", ".wmv",
                ".jpg", ".jpeg", ".png", ".gif", ".bmp",
                ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt"
            ],

            # پسوندهای حذف شده
            "excluded_extensions": [
                ".jpg", ".jpeg", ".png", ".gif", ".bmp",
                ".mp4", ".avi", ".mkv", ".mov"
            ],

            # پوشه‌های استثنا
            "excluded_folders": [
                "System Volume Information",
                "$RECYCLE.BIN",
                "Windows",
                "Program Files"
            ],

            # تنظیمات UI
            "dark_mode": True,
            "colors": {
                "background": [43, 58, 68],
                "panel": [43, 69, 60],
                "text": [230, 210, 181],
                "button": [60, 179, 113],
                "delete_button": [220, 53, 69]
            }
        }

        # بارگذاری از فایل اگر وجود دارد
        self.load()

    def load(self):
        """بارگذاری تنظیمات از فایل"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    # ادغام تنظیمات
                    self._deep_update(self.settings, saved_settings)
        except Exception as e:
            print(f"خطا در بارگذاری تنظیمات: {e}")

    def save(self):
        """ذخیره تنظیمات در فایل"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"خطا در ذخیره تنظیمات: {e}")
            return False

    def get(self, key, default=None):
        """دریافت مقدار تنظیمات"""
        keys = key.split('.')
        value = self.settings
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key, value):
        """تنظیم مقدار"""
        keys = key.split('.')
        settings = self.settings

        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]

        settings[keys[-1]] = value
        return self.save()

    def _deep_update(self, d, u):
        """به‌روزرسانی عمیق دیکشنری"""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v
        return d

    def reset_to_defaults(self):
        """بازنشانی به تنظیمات پیش‌فرض"""
        self._init_config()
        return self.save()


# Singleton instance
config = AppConfig()
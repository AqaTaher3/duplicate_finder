# file_hasher.py
import os
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor
import functools


class FileHasher:
    def __init__(self, max_workers=None):
        self.cache = {}
        self.music_exts = {'.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma'}
        self.ignored_exts = {'.opf', '.db', '.json', '.py', '.jpg', '.ini', '.mp4',
                             '.ebup', '.pdf', '.epub', '.txt', '.doc', '.docx'}
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)

    def _hash_music_optimized(self, file_path):
        """هش‌گذاری بهینه‌شده با بافر بزرگتر"""
        hasher = hashlib.sha256()
        try:
            file_size = os.path.getsize(file_path)
            # برای فایل‌های بزرگ، نمونه‌گیری هوشمند
            if file_size > 50 * 1024 * 1024:  # بیش از 50MB
                return self._hash_large_file(file_path)

            with open(file_path, 'rb') as f:
                # بافر بزرگتر برای فایل‌های موسیقی
                for chunk in iter(lambda: f.read(1024 * 1024), b''):  # 1MB chunks
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logging.error(f"خطا در پردازش فایل موزیک: {file_path} - {str(e)}")
            return None

    def _hash_large_file(self, file_path):
        """برای فایل‌های بسیار بزرگ، نمونه‌گیری از چند نقطه"""
        hasher = hashlib.sha256()
        file_size = os.path.getsize(file_path)
        sample_points = [
            (0, 1024 * 1024),  # ابتدا
            (file_size // 3, 1024 * 1024),  # یک سوم
            (file_size // 2, 1024 * 1024),  # وسط
            (file_size - 1024 * 1024, 1024 * 1024)  # انتها
        ]

        try:
            with open(file_path, 'rb') as f:
                for offset, size in sample_points:
                    if offset < file_size:
                        f.seek(offset)
                        chunk = f.read(size)
                        if chunk:
                            hasher.update(chunk)
                # همچنین اندازه فایل را هم به هش اضافه کن
                hasher.update(str(file_size).encode())
            return hasher.hexdigest()
        except Exception as e:
            logging.error(f"خطا در پردازش فایل بزرگ: {file_path} - {str(e)}")
            return self._hash_music_simple(file_path)

    def _hash_music_simple(self, file_path):
        """روش ساده برای فایل‌های مشکل‌دار"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(256 * 1024), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return None

    def hash_file(self, file_path):
        if not self.check_file_health(file_path):
            return None

        ext = os.path.splitext(file_path)[1].lower()
        return self._hash_music_optimized(file_path) if ext in self.music_exts else None

    @staticmethod
    def check_file_health(file_path):
        try:
            return (os.path.exists(file_path) and
                    os.path.isfile(file_path) and
                    os.path.getsize(file_path) > 0)
        except OSError:
            return False

    def hash_files_batch(self, file_paths):
        """هش‌گذاری دسته‌ای برای کارایی بهتر"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(self.hash_file, file_paths))
        return results
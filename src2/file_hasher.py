import os
import hashlib
import mmap
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import sqlite3
import pickle
import zlib
from pathlib import Path
from src.log_manager import log_manager
from typing import Optional, Dict, Set, List, Tuple


class FileHasher:
    """کلاس بهینه‌سازی شده برای هش کردن فایل‌ها"""

    def __init__(self, max_workers: int = None, cache_enabled: bool = True):
        self.cache_enabled = cache_enabled
        self.music_exts: Set[str] = {'.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma'}
        self.video_exts: Set[str] = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'}
        self.image_exts: Set[str] = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
        self.ignored_exts: Set[str] = {'.opf', '.db', '.json', '.py', '.ini', '.tmp', '.log'}

        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) * 2)
        self.logger = log_manager.get_logger("FileHasher")

        # کش حافظه
        self.memory_cache: Dict[str, str] = {}
        self.cache_max_size = 1000

        # کش پایگاه داده - در child processها ایجاد نکن
        self.db_cache = None
        if cache_enabled and not self._is_child_process():
            try:
                self.db_cache = HashCache()
            except Exception as e:
                self.logger.warning(f"خطا در ایجاد کش دیتابیس: {e}")

        self.logger.info(f"FileHasher با {self.max_workers} worker راه‌اندازی شد")


    def _is_child_process(self):
        """بررسی آیا در فرایند child هستیم"""
        import multiprocessing
        try:
            return multiprocessing.current_process().name != 'MainProcess'
        except:
            return False

    def hash_file(self, file_path: str) -> Optional[str]:
        """هش کردن فایل با استفاده از بهترین روش"""
        try:
            # بررسی سلامت فایل
            if not self.check_file_health(file_path):
                self.logger.warning(f"فایل نامعتبر: {file_path}")
                return None

            # بررسی کش حافظه
            if file_path in self.memory_cache:
                return self.memory_cache[file_path]

            # بررسی کش دیتابیس
            if self.db_cache:
                cached_hash = self.db_cache.get(file_path)
                if cached_hash:
                    self.memory_cache[file_path] = cached_hash
                    if len(self.memory_cache) > self.cache_max_size:
                        self.memory_cache.pop(next(iter(self.memory_cache)))
                    return cached_hash

            # تشخیص نوع فایل و انتخاب روش مناسب
            ext = Path(file_path).suffix.lower()
            file_hash = None

            if ext in self.music_exts:
                file_hash = self._hash_music_optimized(file_path)
            elif ext in self.video_exts:
                file_hash = self._hash_video_optimized(file_path)
            elif ext in self.image_exts:
                file_hash = self._hash_image_optimized(file_path)
            else:
                file_hash = self._hash_generic_optimized(file_path)

            # ذخیره در کش‌ها
            if file_hash:
                self.memory_cache[file_path] = file_hash
                if len(self.memory_cache) > self.cache_max_size:
                    self.memory_cache.pop(next(iter(self.memory_cache)))

                if self.db_cache:
                    self.db_cache.set(file_path, file_hash)

            return file_hash

        except Exception as e:
            self.logger.error(f"خطا در هش کردن {file_path}: {e}")
            return None

    def _hash_music_optimized(self, file_path: str) -> Optional[str]:
        """هش بهینه برای فایل‌های موسیقی"""
        try:
            file_size = os.path.getsize(file_path)
            hasher = hashlib.sha256()

            # برای فایل‌های کوچک، هش کامل
            if file_size < 10 * 1024 * 1024:  # کمتر از 10MB
                return self._hash_full_file(file_path, hasher)

            # برای فایل‌های بزرگ، نمونه‌گیری هوشمند
            sample_points = self._calculate_sample_points(file_size)

            with open(file_path, 'rb') as f:
                # خواندن نمونه‌ها از نقاط کلیدی
                for offset, size in sample_points:
                    if offset < file_size:
                        f.seek(offset)
                        chunk = f.read(size)
                        if chunk:
                            hasher.update(chunk)

                # اضافه کردن متادیتا
                hasher.update(str(file_size).encode())
                hasher.update(str(os.path.getmtime(file_path)).encode())

            return hasher.hexdigest()

        except Exception as e:
            self.logger.error(f"خطا در هش موسیقی {file_path}: {e}")
            return self._hash_generic_fallback(file_path)

    def _hash_video_optimized(self, file_path: str) -> Optional[str]:
        """هش بهینه برای فایل‌های ویدیویی"""
        try:
            file_size = os.path.getsize(file_path)
            hasher = hashlib.sha256()

            # ویدیوها معمولاً بزرگ هستند، نمونه‌گیری لازم است
            if file_size > 100 * 1024 * 1024:  # بیشتر از 100MB
                return self._hash_large_file_sampled(file_path)

            return self._hash_full_file(file_path, hasher)

        except Exception as e:
            self.logger.error(f"خطا در هش ویدیو {file_path}: {e}")
            return self._hash_generic_fallback(file_path)

    def _hash_image_optimized(self, file_path: str) -> Optional[str]:
        """هش بهینه برای تصاویر"""
        try:
            # تصاویر معمولاً کوچک هستند، هش کامل
            return self._hash_full_file(file_path, hashlib.sha256())
        except Exception as e:
            self.logger.error(f"خطا در هش تصویر {file_path}: {e}")
            return None

    def _hash_generic_optimized(self, file_path: str) -> Optional[str]:
        """هش عمومی بهینه‌سازی شده"""
        try:
            file_size = os.path.getsize(file_path)

            if file_size > 50 * 1024 * 1024:  # بیشتر از 50MB
                return self._hash_large_file_sampled(file_path)

            return self._hash_full_file(file_path, hashlib.sha256())
        except Exception as e:
            self.logger.error(f"خطا در هش عمومی {file_path}: {e}")
            return None

    def _hash_full_file(self, file_path: str, hasher) -> str:
        """هش کامل فایل"""
        try:
            with open(file_path, 'rb') as f:
                # استفاده از mmap برای کارایی بهتر
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
                    # پردازش در بلوک‌های بزرگ
                    chunk_size = 1024 * 1024  # 1MB
                    for i in range(0, len(m), chunk_size):
                        chunk = m[i:i + chunk_size]
                        hasher.update(chunk)

            return hasher.hexdigest()
        except Exception as e:
            raise Exception(f"خطا در هش کامل: {e}")

    def _hash_large_file_sampled(self, file_path: str) -> str:
        """هش فایل‌های بسیار بزرگ با نمونه‌گیری"""
        try:
            file_size = os.path.getsize(file_path)
            hasher = hashlib.sha256()

            # نقاط نمونه‌گیری هوشمند
            sample_points = self._calculate_sample_points(file_size)

            with open(file_path, 'rb') as f:
                for offset, size in sample_points:
                    if offset < file_size:
                        f.seek(offset)
                        chunk = f.read(size)
                        if chunk:
                            hasher.update(chunk)

                # اضافه کردن اطلاعات فایل
                hasher.update(str(file_size).encode())
                hasher.update(str(os.path.getmtime(file_path)).encode())

            return hasher.hexdigest()
        except Exception as e:
            raise Exception(f"خطا در هش نمونه‌گیری: {e}")

    def _calculate_sample_points(self, file_size: int) -> List[Tuple[int, int]]:
        """محاسبه نقاط نمونه‌گیری هوشمند"""
        sample_size = min(1024 * 1024, file_size // 100)  # 1MB یا 1% فایل

        points = []

        # ابتدای فایل (همیشه)
        points.append((0, sample_size))

        # اگر فایل بزرگ است، نقاط بیشتری اضافه کن
        if file_size > 10 * 1024 * 1024:  # بیشتر از 10MB
            points.append((file_size // 4, sample_size))  # 25%
            points.append((file_size // 2, sample_size))  # 50%
            points.append((file_size * 3 // 4, sample_size))  # 75%

        # انتهای فایل (همیشه)
        points.append((max(0, file_size - sample_size), sample_size))

        return points

    def _hash_generic_fallback(self, file_path: str) -> Optional[str]:
        """روش fallback برای هش کردن"""
        try:
            hasher = hashlib.md5()  # استفاده از MD5 برای سرعت بیشتر
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return None

    @staticmethod
    def check_file_health(file_path: str) -> bool:
        """بررسی سلامت فایل"""
        try:
            return (os.path.exists(file_path) and
                    os.path.isfile(file_path) and
                    os.path.getsize(file_path) > 0)
        except OSError:
            return False

    def hash_files_batch(self, file_paths: List[str]) -> List[Optional[str]]:
        """هش دسته‌ای فایل‌ها"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(self.hash_file, file_paths))
        return results

    def clear_cache(self):
        """پاک کردن کش"""
        self.memory_cache.clear()
        if self.db_cache:
            self.db_cache.clear()


class HashCache:
    """سیستم کش پایگاه داده"""

    def __init__(self, cache_file: str = 'hash_cache.db'):
        self.cache_file = cache_file
        self.conn = None
        self._init_db()

    def __getstate__(self):
        """برای pickle کردن - connection را حذف کن"""
        state = self.__dict__.copy()
        state['conn'] = None  # connection را حذف کن
        return state

    def __setstate__(self, state):
        """برای unpickle کردن"""
        self.__dict__.update(state)
        if self.cache_file:
            self._init_db()

    def _init_db(self):
        """راه‌اندازی پایگاه داده"""
        try:
            if self.conn is None:
                self.conn = sqlite3.connect(self.cache_file, timeout=10)
                self.conn.execute('''
                    CREATE TABLE IF NOT EXISTS file_hashes (
                        path TEXT PRIMARY KEY,
                        hash TEXT NOT NULL,
                        size INTEGER NOT NULL,
                        mtime REAL NOT NULL,
                        created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                self.conn.execute('CREATE INDEX IF NOT EXISTS idx_hash ON file_hashes(hash)')
                self.conn.execute('CREATE INDEX IF NOT EXISTS idx_mtime ON file_hashes(mtime)')
                self.conn.commit()
        except Exception as e:
            print(f"خطا در راه‌اندازی کش: {e}")
            self.conn = None

    def get(self, file_path: str) -> Optional[str]:
        """دریافت هش از کش"""
        if not self.conn:
            return None

        try:
            size = os.path.getsize(file_path)
            mtime = os.path.getmtime(file_path)

            cursor = self.conn.execute(
                'SELECT hash FROM file_hashes WHERE path = ? AND size = ? AND mtime = ?',
                (file_path, size, mtime)
            )
            result = cursor.fetchone()
            return result[0] if result else None
        except:
            return None

    def set(self, file_path: str, hash_value: str) -> bool:
        """ذخیره هش در کش"""
        if not self.conn:
            return False

        try:
            size = os.path.getsize(file_path)
            mtime = os.path.getmtime(file_path)

            self.conn.execute(
                'INSERT OR REPLACE INTO file_hashes (path, hash, size, mtime) VALUES (?, ?, ?, ?)',
                (file_path, hash_value, size, mtime)
            )
            self.conn.commit()
            return True
        except:
            return False

    def clear(self):
        """پاک کردن کش"""
        if self.conn:
            try:
                self.conn.execute('DELETE FROM file_hashes')
                self.conn.commit()
            except:
                pass

    def cleanup_old(self, days: int = 30):
        """حذف رکوردهای قدیمی"""
        if self.conn:
            try:
                self.conn.execute(
                    'DELETE FROM file_hashes WHERE created < datetime("now", ?)',
                    (f"-{days} days",)
                )
                self.conn.commit()
            except:
                pass

    def __del__(self):
        """تخریب شی"""
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
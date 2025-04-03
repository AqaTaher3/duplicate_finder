import os
import hashlib
import wx
from tqdm import tqdm
import time

class FileFinder:
    def __init__(self, folder_path, exclude_folders=None, progress_bar=None, progress_label=None, log_callback=None, ui_update_callback=None):
        self.folder_path = folder_path
        self.exclude_folders = [os.path.normpath(f) for f in (exclude_folders or [])]  # نرمالایز مسیرها
        self.progress_bar = progress_bar
        self.progress_label = progress_label
        self.log_callback = log_callback
        self.ui_update_callback = ui_update_callback  # کالبک برای به‌روزرسانی UI
        self.last_update_time = time.time()
        self.last_update_count = 0

    def _log(self, message):
        if self.log_callback:
            wx.CallAfter(self.log_callback, message)
        else:
            print(message)

    def _should_skip(self, root):
        """بررسی آیا مسیر جستجو باید نادیده گرفته شود"""
        current_path = os.path.normpath(root)
        for excluded in self.exclude_folders:
            if current_path.startswith(excluded):
                return True
        return False

    def _hash_file(self, file_path):
        """محاسبه هش SHA-256 برای فایل"""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):  # خواندن به صورت قطعات 8KB
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, IOError) as e:
            self._log(f"⚠️ Error reading {file_path}: {str(e)}")
            return None

    def find_files(self):
        """تابع اصلاح شده برای نمایش یکپارچه اطلاعات"""
        file_hashes = {}
        total_files = 0
        start_time = time.time()

        # محاسبه تعداد فایل‌ها با فرمت صحیح فارسی
        self._log("🔍 در حال محاسبه تعداد فایل‌ها...")
        for root, dirs, files in os.walk(self.folder_path):
            if self._should_skip(root):
                dirs[:] = []
                continue
            total_files += len(files)

        self._log(f"📂 تعداد فایل‌ها برای اسکن: {total_files}")
        self._update_ui(total_files, 0, 0)

        # تنظیمات progress bar برای نمایش صحیح فارسی
        with tqdm(total=total_files, desc="پیشرفت اسکن", unit="فایل",
                  bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{rate_fmt}]") as pbar:

            processed_files = 0
            for root, dirs, files in os.walk(self.folder_path):
                if self._should_skip(root):
                    dirs[:] = []
                    continue

                for filename in files:
                    file_path = os.path.join(root, filename)

                    if not self._check_file_health(file_path):
                        processed_files += 1
                        pbar.update(1)
                        continue

                    file_hash = self._hash_file(file_path)
                    if file_hash:
                        file_hashes.setdefault(file_hash, []).append(file_path)

                    processed_files += 1
                    pbar.update(1)

                    # به‌روزرسانی هر 0.5 ثانیه
                    if time.time() - start_time > 0.5:
                        speed = processed_files / (time.time() - start_time)
                        self._update_ui(total_files, processed_files, speed)

        duplicate_groups = [group for group in file_hashes.values() if len(group) > 1]
        self._log(f"✅ تعداد گروه‌های تکراری یافت شده: {len(duplicate_groups)}")
        self._update_ui(total_files, total_files, total_files / (time.time() - start_time))

        return duplicate_groups

    def _update_ui(self, total, scanned, speed):
        """به‌روزرسانی رابط کاربری با اطلاعات جدید"""
        if self.ui_update_callback:
            wx.CallAfter(self.ui_update_callback, {
                'total_files': total,
                'scanned_files': scanned,
                'speed': speed,
                'remaining': total - scanned,
                'percentage': (scanned / total) * 100 if total > 0 else 0
            })
    @staticmethod
    def _check_file_health(file_path):
        """بررسی سلامت فایل"""
        try:
            return (os.path.exists(file_path) and
                    os.path.isfile(file_path) and
                    os.path.getsize(file_path) > 0)
        except OSError:
            return False
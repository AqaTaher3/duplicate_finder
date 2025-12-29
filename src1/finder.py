import os
import wx
import time
import hashlib
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import functools
from src2.file_hasher import FileHasher
import collections
from src.log_manager import log_manager


class FileFinder:
    def __init__(self, folder_path, exclude_folders=None, progress_bar=None,
                 progress_label=None, log_callback=None, ui_update_callback=None,
                 cache_file=None, batch_size=1000):
        self.folder_path = folder_path
        self.exclude_folders = [os.path.normpath(f) for f in (exclude_folders or [])]
        self.progress_bar = progress_bar
        self.progress_label = progress_label
        self.log_callback = log_callback
        self.ui_update_callback = ui_update_callback
        self.hasher = FileHasher()
        self.batch_size = batch_size

        # لیست فرمت‌های قابل پردازش
        self.supported_extensions = {
            '.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma',
            '.mp4', '.avi', '.mkv', '.mov', '.wmv',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt'
        }

        self.logger = log_manager.get_logger("FileFinder")
        self.logger.info(f"FileFinder ساخته شد برای: {folder_path}")

    def _is_child_process(self):
        """بررسی آیا در فرایند child هستیم"""
        import multiprocessing
        try:
            return multiprocessing.current_process().name != 'MainProcess'
        except:
            return True

    def _log(self, message, level='info'):
        """Log messages with callback support"""
        if self.log_callback:
            wx.CallAfter(self.log_callback, message)

        if self.logger:
            if level == 'info':
                self.logger.info(message)
            elif level == 'warning':
                self.logger.warning(message)
            elif level == 'error':
                self.logger.error(message)
            elif level == 'debug':
                self.logger.debug(message)

    def _should_skip(self, root):
        """Check if path should be skipped"""
        current_path = os.path.normpath(root)

        # پرش پوشه‌های سیستمی
        if any(skip in current_path.lower() for skip in ['system', 'windows', '$recycle.bin', 'appdata']):
            return True

        for excluded in self.exclude_folders:
            if current_path.startswith(excluded):
                return True
        return False

    def _is_supported_file(self, filename):
        """بررسی آیا فایل پشتیبانی می‌شود"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.supported_extensions

    def _update_ui(self, total, scanned, speed, duplicates_found, status=""):
        """Update UI with Persian formatted messages"""
        if self.ui_update_callback:
            wx.CallAfter(self.ui_update_callback, {
                'total_files': total,
                'scanned_files': scanned,
                'speed': speed,
                'remaining': total - scanned,
                'percentage': (scanned / total) * 100 if total > 0 else 0,
                'duplicates': duplicates_found,
                'message': f"پردازش شده: {scanned}/{total} | سرعت: {speed:.1f} فایل/ثانیه | تکراری‌ها: {duplicates_found}",
                'status': status
            })

    def _build_size_map_optimized(self):
        """ساخت نقشه سایز با کارایی بهتر"""
        size_map = collections.defaultdict(list)
        total_files = 0
        supported_files = 0

        self._log("📂 در حال اسکن فایل‌ها...")

        start_time = time.time()

        try:
            for root, dirs, files in os.walk(self.folder_path):
                # فیلتر کردن پوشه‌ها در همان لحظه
                dirs[:] = [d for d in dirs if not self._should_skip(os.path.join(root, d))]

                if self._should_skip(root):
                    continue

                for filename in files:
                    # فیلتر فرمت‌های پشتیبانی شده
                    if not self._is_supported_file(filename):
                        continue

                    file_path = os.path.join(root, filename)
                    if not self.hasher.check_file_health(file_path):
                        continue

                    try:
                        file_size = os.path.getsize(file_path)
                        size_map[file_size].append(file_path)
                        total_files += 1
                        supported_files += 1
                    except OSError:
                        continue

            elapsed = time.time() - start_time
            self._log(f"✅ اسکن فایل‌ها کامل شد. زمان: {elapsed:.2f} ثانیه")
            self._log(f"📊 آمار: {total_files} فایل کل، {supported_files} فایل پشتیبانی شده")

        except Exception as e:
            self._log(f"❌ خطا در اسکن فایل‌ها: {str(e)}", 'error')
            raise

        return size_map, total_files

    def _process_batch(self, file_batch):
        """پردازش یک دسته فایل - بهینه‌سازی شده"""
        results = []
        for file_path in file_batch:
            try:
                file_hash = self.hasher.hash_file(file_path)
                if file_hash:  # فقط اگر هش معتبر باشد
                    results.append((file_hash, file_path))
            except Exception as e:
                self.logger.debug(f"خطا در پردازش {file_path}: {e}")
                continue
        return results

    def find_files(self):
        """Main method to find duplicate files"""
        start_time = time.time()
        self._log("🔍 شروع فرآیند یافتن فایل‌های تکراری...")

        try:
            # First pass - count files and build size map
            size_map, total_files = self._build_size_map_optimized()

            if total_files == 0:
                self._log("❌ هیچ فایلی برای پردازش یافت نشد")
                return []

            # Only process files that have size duplicates
            candidate_files = []
            duplicate_size_count = 0

            for size, files in size_map.items():
                if len(files) > 1:
                    candidate_files.extend(files)
                    duplicate_size_count += len(files)

            self._log(f"📊 فایل‌های کاندید: {len(candidate_files)} از {duplicate_size_count} فایل با سایز تکراری")

            if not candidate_files:
                self._log("✅ هیچ فایل کاندیدی برای بررسی هش یافت نشد")
                return []

            # Process files in parallel with progress reporting
            file_hashes = {}
            last_update = time.time()

            # محاسبه تعداد workerها
            cpu_count = os.cpu_count() or 1
            max_workers = min(cpu_count, 8)  # حداکثر 8 worker

            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                process_func = functools.partial(self._process_file_wrapper)

                # ایجاد progress bar
                with tqdm(total=len(candidate_files), desc="پردازش هش", unit="فایل",
                          bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{rate_fmt}]") as pbar:

                    futures = {executor.submit(process_func, file_path): file_path
                               for file_path in candidate_files}

                    for future in as_completed(futures):
                        try:
                            file_hash, file_path = future.result(timeout=30)
                            if file_hash and file_path:
                                file_hashes.setdefault(file_hash, []).append(file_path)
                        except Exception as e:
                            self.logger.warning(f"خطا در پردازش فایل: {e}")

                        pbar.update(1)

                        # آپدیت UI هر 0.5 ثانیه
                        current_time = time.time()
                        if current_time - last_update > 0.5:
                            speed = pbar.n / (current_time - start_time)
                            duplicates = sum(1 for group in file_hashes.values() if len(group) > 1)
                            self._update_ui(len(candidate_files), pbar.n, speed, duplicates,
                                            f"پردازش هش: {pbar.n}/{len(candidate_files)}")
                            last_update = current_time

            # Final results
            duplicate_groups = [group for group in file_hashes.values() if len(group) > 1]

            # لاگ‌گیری نتایج
            elapsed_time = time.time() - start_time
            self._log(f"✅ پردازش کامل شد. زمان: {elapsed_time:.2f} ثانیه")
            self._log(f"📊 نتایج: {len(duplicate_groups)} گروه تکراری یافت شد")

            if duplicate_groups:
                total_duplicates = sum(len(g) - 1 for g in duplicate_groups)
                self._log(f"🗑️  تعداد فایل‌های تکراری قابل حذف: {total_duplicates}")

            return duplicate_groups

        except Exception as e:
            self._log(f"❌ خطا در فرآیند یافتن فایل‌های تکراری: {str(e)}", 'error')
            raise

    def _process_file_wrapper(self, file_path):
        """Wrapper for parallel processing"""
        try:
            return self.hasher.hash_file(file_path), file_path
        except Exception as e:
            self.logger.debug(f"خطا در wrapper برای {file_path}: {e}")
            return None, None

    def find_files_quick(self):
        """نسخه سریع برای بررسی اولیه"""
        size_map, total_files = self._build_size_map_optimized()

        # فقط فایل‌هایی که دقیقاً سایز یکسان دارند
        potential_duplicates = []
        for size, files in size_map.items():
            if len(files) > 1:
                # اگر سایز دقیقاً برابر باشد، احتمال تکراری بودن زیاد است
                potential_duplicates.append(files)

        return potential_duplicates
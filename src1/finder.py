import os
import wx
import time
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import functools
from src2.file_hasher import FileHasher
import collections
from src.log_manager import log_manager
from src.config import config  # ✅ اضافه کردن import


class FileFinder:
    def __init__(self, folder_path, exclude_folders=None, progress_bar=None,
                 progress_label=None, log_callback=None, ui_update_callback=None,
                 cache_file=None, batch_size=1000, progress_callback=None):
        self.folder_path = folder_path
        self.exclude_folders = [os.path.normpath(f) for f in (exclude_folders or [])]
        self.progress_bar = progress_bar
        self.progress_label = progress_label
        self.log_callback = log_callback
        self.ui_update_callback = ui_update_callback
        self.hasher = FileHasher()
        self.batch_size = batch_size or config.get("batch_size", 1000)

        self.supported_extensions = set(config.get("supported_extensions", []))

        # ✅ اضافه کردن last_update_time
        self.last_update_time = time.time()

        # ✅ اضافه کردن hash_times برای FileHasher
        self.hash_times = []

        # ✅ اضافه کردن متغیرهای ضروری
        self.stats = {
            'total_files_scanned': 0,
            'files_processed': 0,
            'hash_time': 0,
            'groups_found': 0
        }

        self.logger = log_manager.get_logger("FileFinder")
        self.logger.info(f"FileFinder ساخته شد برای: {folder_path}")
        self.progress_callback = progress_callback
        self.logger = log_manager.get_logger("FileFinder")

    def _report_progress(self, progress, status=None):
        """گزارش پیشرفت به callback"""
        if self.progress_callback:
            try:
                wx.CallAfter(self.progress_callback, progress, status)
            except Exception as e:
                self.logger.debug(f"خطا در گزارش پیشرفت: {e}")

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
        """ساخت نقشه سایز با کارایی بهتر و گزارش پیشرفت"""
        size_map = collections.defaultdict(list)
        total_files = 0
        supported_files = 0

        self._log("📂 در حال اسکن فایل‌ها...")
        self._report_progress(5, "اسکن فایل‌ها...")

        start_time = time.time()

        try:
            # ✅ شمارش سریع فایل‌ها برای پیشرفت دقیق
            total_files_count = 0
            self._report_progress(3, "شمارش فایل‌ها...")

            for root, dirs, files in os.walk(self.folder_path):
                dirs[:] = [d for d in dirs if not self._should_skip(os.path.join(root, d))]
                if self._should_skip(root):
                    continue
                for filename in files:
                    if self._is_supported_file(filename):
                        total_files_count += 1

            if total_files_count == 0:
                self._report_progress(50, "هیچ فایل پشتیبانی شده‌ای یافت نشد")
                return size_map, 0

            self._report_progress(5, f"اسکن {total_files_count} فایل...")

            processed = 0
            for root, dirs, files in os.walk(self.folder_path):
                dirs[:] = [d for d in dirs if not self._should_skip(os.path.join(root, d))]

                if self._should_skip(root):
                    continue

                for filename in files:
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

                    processed += 1
                    # ✅ گزارش پیشرفت هر 50 فایل
                    if processed % 50 == 0 and total_files_count > 0:
                        progress = 5 + (processed / total_files_count) * 45  # 5% تا 50%
                        self._report_progress(progress, f"اسکن: {processed}/{total_files_count}")
                        wx.Yield()  # اجازه می‌دهد UI به‌روز شود

            elapsed = time.time() - start_time
            self._log(f"✅ اسکن فایل‌ها کامل شد. زمان: {elapsed:.2f} ثانیه")
            self._report_progress(50, f"اسکن کامل شد: {total_files} فایل")

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
        self._report_progress(0, "شروع پردازش...")

        self.last_update_time = start_time

        self.stats = {
            'total_files': 0,
            'files_processed': 0,
            'hash_time': 0,
            'groups_found': 0,
            'start_time': start_time
        }

        try:
            # First pass - count files and build size map
            self._report_progress(5, "ساخت نقشه سایز فایل‌ها...")
            size_map, total_files = self._build_size_map_optimized()
            self.stats['total_files'] = total_files

            if total_files == 0:
                self._log("❌ هیچ فایلی برای پردازش یافت نشد")
                self._report_progress(100, "هیچ فایلی یافت نشد")
                return []

            # Only process files that have size duplicates
            candidate_files = []
            duplicate_size_count = 0

            for size, files in size_map.items():
                if len(files) > 1:
                    candidate_files.extend(files)
                    duplicate_size_count += len(files)

            self._log(f"📊 فایل‌های کاندید: {len(candidate_files)} از {duplicate_size_count} فایل با سایز تکراری")
            self._report_progress(55, f"یافت شد {len(candidate_files)} فایل کاندید")

            if not candidate_files:
                self._log("✅ هیچ فایل کاندیدی برای بررسی هش یافت نشد")
                self._report_progress(100, "هیچ تکراری یافت نشد")
                return []

            # ✅ برای تست: از پردازش تک‌تردی استفاده کن (برای رفع مشکل Pickle)
            self._report_progress(60, "شروع هش کردن فایل‌ها...")

            file_hashes = {}
            hash_start_time = time.time()

            total = len(candidate_files)
            completed = 0

            # ✅ استفاده از پردازش تک‌تردی به جای Multiprocessing
            for file_path in candidate_files:
                try:
                    file_hash = self.hasher.hash_file(file_path)
                    if file_hash:
                        file_hashes.setdefault(file_hash, []).append(file_path)
                        self.stats['files_processed'] += 1
                except Exception as e:
                    self.logger.warning(f"خطا در پردازش فایل: {e}")

                completed += 1

                # گزارش پیشرفت هر 10 فایل
                if completed % 10 == 0:
                    progress = 60 + (completed / total) * 35
                    speed = completed / (time.time() - start_time)
                    self._report_progress(progress,
                                          f"هش کردن: {completed}/{total} ({speed:.1f} فایل/ثانیه)")

            # Final results
            duplicate_groups = [group for group in file_hashes.values() if len(group) > 1]
            self.stats['groups_found'] = len(duplicate_groups)
            self.stats['hash_time'] = time.time() - hash_start_time

            elapsed_time = time.time() - start_time
            self._log(f"✅ پردازش کامل شد. زمان: {elapsed_time:.2f} ثانیه")

            if duplicate_groups:
                total_duplicates = sum(len(g) - 1 for g in duplicate_groups)
                self._log(f"🗑️ تعداد فایل‌های تکراری قابل حذف: {total_duplicates}")
                self._report_progress(100, f"✅ یافت شد: {len(duplicate_groups)} گروه، {total_duplicates} تکراری")
            else:
                self._report_progress(100, "✅ هیچ فایل تکراری یافت نشد")

            return duplicate_groups

        except Exception as e:
            self._log(f"❌ خطا در فرآیند یافتن فایل‌های تکراری: {str(e)}", 'error')
            self._report_progress(100, f"❌ خطا: {str(e)}")
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
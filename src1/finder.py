import os
import wx
import time
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import functools
from src2.file_hasher import FileHasher
import collections


class FileFinder:
    def __init__(self, folder_path, exclude_folders=None, progress_bar=None,
                 progress_label=None, log_callback=None, ui_update_callback=None,
                 cache_file=None, batch_size=1000):
        """
        Initialize FileFinder with UI capabilities
        """
        self.folder_path = folder_path
        self.exclude_folders = [os.path.normpath(f) for f in (exclude_folders or [])]
        self.progress_bar = progress_bar
        self.progress_label = progress_label
        self.log_callback = log_callback
        self.ui_update_callback = ui_update_callback
        self.hasher = FileHasher()
        self.batch_size = batch_size

    def _log(self, message):
        """Log messages with callback support"""
        if self.log_callback:
            wx.CallAfter(self.log_callback, message)
        else:
            print(message)

    def _should_skip(self, root):
        """Check if path should be skipped"""
        current_path = os.path.normpath(root)
        for excluded in self.exclude_folders:
            if current_path.startswith(excluded):
                return True
        return False

    def _update_ui(self, total, scanned, speed, duplicates_found):
        """Update UI with Persian formatted messages"""
        if self.ui_update_callback:
            wx.CallAfter(self.ui_update_callback, {
                'total_files': total,
                'scanned_files': scanned,
                'speed': speed,
                'remaining': total - scanned,
                'percentage': (scanned / total) * 100 if total > 0 else 0,
                'duplicates': duplicates_found,
                'message': f"پردازش شده: {scanned}/{total} | سرعت: {speed:.1f} فایل/ثانیه | تکراری‌ها: {duplicates_found}"
            })

    def _build_size_map_optimized(self):
        """ساخت نقشه سایز با کارایی بهتر"""
        size_map = collections.defaultdict(list)
        total_files = 0

        self._log("📂 در حال اسکن فایل‌ها...")

        for root, dirs, files in os.walk(self.folder_path):
            # فیلتر کردن پوشه‌ها در همان لحظه
            dirs[:] = [d for d in dirs if not self._should_skip(os.path.join(root, d))]

            if self._should_skip(root):
                continue

            for filename in files:
                file_path = os.path.join(root, filename)
                if not self.hasher.check_file_health(file_path):
                    continue

                try:
                    file_size = os.path.getsize(file_path)
                    size_map[file_size].append(file_path)
                    total_files += 1
                except OSError:
                    continue

        return size_map, total_files

    def _process_file_wrapper(self, file_path):
        """Wrapper for parallel processing"""
        return self.hasher.hash_file(file_path), file_path

    def _process_batch(self, file_batch):
        """پردازش یک دسته فایل"""
        results = []
        for file_path in file_batch:
            file_hash = self.hasher.hash_file(file_path)
            results.append((file_hash, file_path))
        return results

    def find_files(self):
        """Main method to find duplicate files - نسخه اصلی برای حفظ سازگاری"""
        start_time = time.time()
        self._log("🔍 شروع فرآیند یافتن فایل‌های تکراری...")

        # First pass - count files and build size map
        size_map = {}
        total_files = 0
        self._log("📂 در حال محاسبه تعداد فایل‌ها...")

        for root, dirs, files in os.walk(self.folder_path):
            if self._should_skip(root):
                dirs[:] = []
                continue

            for filename in files:
                file_path = os.path.join(root, filename)
                if not self.hasher.check_file_health(file_path):
                    continue

                file_size = os.path.getsize(file_path)
                size_map.setdefault(file_size, []).append(file_path)
                total_files += 1

        self._log(f"📂 تعداد کل فایل‌ها: {total_files}")

        # Only process files that have size duplicates
        candidate_files = [f for group in size_map.values() if len(group) > 1 for f in group]
        self._log(f"🔍 تعداد فایل‌های کاندید برای بررسی تکراری: {len(candidate_files)}")

        # Process files in parallel with progress reporting
        file_hashes = {}
        processed_files = 0
        last_update = time.time()

        with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
            process_func = functools.partial(self._process_file_wrapper)

            # Persian formatted progress bar
            with tqdm(total=len(candidate_files), desc="پیشرفت پردازش", unit="فایل",
                      bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{rate_fmt}]") as pbar:

                for file_hash, file_path in executor.map(process_func, candidate_files):
                    if file_hash and file_path:
                        file_hashes.setdefault(file_hash, []).append(file_path)

                    processed_files += 1
                    pbar.update(1)

                    # Update UI every 0.5 seconds
                    if time.time() - last_update > 0.5:
                        speed = processed_files / (time.time() - start_time)
                        duplicates = sum(1 for group in file_hashes.values() if len(group) > 1)
                        self._update_ui(len(candidate_files), processed_files, speed, duplicates)
                        last_update = time.time()

        # Final results
        duplicate_groups = [group for group in file_hashes.values() if len(group) > 1]
        self._log(f"✅ پردازش کامل شد. تعداد گروه‌های تکراری یافت شده: {len(duplicate_groups)}")
        self._update_ui(len(candidate_files), len(candidate_files),
                        len(candidate_files) / (time.time() - start_time), len(duplicate_groups))

        return duplicate_groups

    def find_files_optimized(self):
        """نسخه بهینه‌شده برای سرعت بیشتر - اختیاری"""
        start_time = time.time()
        self._log("🔍 شروع فرآیند یافتن فایل‌های تکراری (نسخه بهینه)...")

        # ساخت نقشه سایز
        size_map, total_files = self._build_size_map_optimized()
        self._log(f"📂 تعداد کل فایل‌ها: {total_files}")

        # فقط فایل‌های با سایز تکراری
        candidate_files = []
        for size_group in size_map.values():
            if len(size_group) > 1:
                candidate_files.extend(size_group)

        self._log(f"🔍 تعداد فایل‌های کاندید: {len(candidate_files)}")

        if not candidate_files:
            return []

        # پردازش دسته‌ای برای مدیریت حافظه بهتر
        file_hashes = {}
        batch_duplicates = 0

        with ProcessPoolExecutor(max_workers=min(os.cpu_count(), 8)) as executor:
            futures = {}

            # ارسال دسته‌ای کارها
            for i in range(0, len(candidate_files), self.batch_size):
                batch = candidate_files[i:i + self.batch_size]
                future = executor.submit(self._process_batch, batch)
                futures[future] = batch

            # پردازش نتایج به محض آماده شدن
            with tqdm(total=len(candidate_files), desc="پردازش", unit="فایل") as pbar:
                for future in as_completed(futures):
                    batch_results = future.result()
                    batch_files = futures[future]

                    for file_hash, file_path in batch_results:
                        if file_hash and file_path:
                            if file_hash in file_hashes:
                                file_hashes[file_hash].append(file_path)
                                if len(file_hashes[file_hash]) == 2:  # اولین بار که تکراری پیدا شد
                                    batch_duplicates += 1
                            else:
                                file_hashes[file_hash] = [file_path]

                    pbar.update(len(batch_files))

                    # آپدیت UI
                    speed = pbar.n / (time.time() - start_time)
                    self._update_ui(len(candidate_files), pbar.n, speed, batch_duplicates)

        duplicate_groups = [group for group in file_hashes.values() if len(group) > 1]
        self._log(f"✅ پردازش کامل شد. گروه‌های تکراری: {len(duplicate_groups)}")

        return duplicate_groups
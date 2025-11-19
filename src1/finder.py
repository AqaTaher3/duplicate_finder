import os
import wx
import time
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
import functools
from src2.file_hasher import FileHasher


class FileFinder:
    def __init__(self, folder_path, exclude_folders=None, progress_bar=None,
                 progress_label=None, log_callback=None, ui_update_callback=None,
                 cache_file=None):
        """
        Initialize FileFinder with UI capabilities

        :param folder_path: Root directory to scan
        :param exclude_folders: Folders to exclude from search
        :param progress_bar: wxPython progress bar
        :param progress_label: wxPython label for progress
        :param log_callback: Callback for logging messages
        :param ui_update_callback: Callback for UI updates
        :param cache_file: Path to cache file for faster subsequent runs
        """
        self.folder_path = folder_path
        self.exclude_folders = [os.path.normpath(f) for f in (exclude_folders or [])]
        self.progress_bar = progress_bar
        self.progress_label = progress_label
        self.log_callback = log_callback
        self.ui_update_callback = ui_update_callback
        self.hasher = FileHasher()

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
                'message': f"پردازش شده: {scanned}/{total} | سرعت: {speed:.1f} فایل/ثانیه | تکراری‌ها: "
                           f"{duplicates_found}"
            })

    def _process_file_wrapper(self, file_path):
        """Wrapper for parallel processing"""
        return self.hasher.hash_file(file_path), file_path

    def find_files(self):
        """Main method to find duplicate files with all features"""
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
        self._log(f"number of duplicate file: {duplicate_groups}")
        print(len(duplicate_groups))

        return duplicate_groups

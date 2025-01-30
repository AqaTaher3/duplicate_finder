import os
import hashlib
import wx
from tqdm import tqdm  # اضافه کردن کتابخانه tqdm

class FileFinder:
    def __init__(self, folder_path, progress_bar=None, progress_label=None):
        self.folder_path = folder_path
        self.progress_bar = progress_bar
        self.progress_label = progress_label

    def _hash_file(self, file_path):
        """Generate SHA-256 hash for a file."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):  # Read in chunks to handle large files
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, IOError) as e:
            print(f"Error reading file {file_path}: {str(e)}")
            return None

    def find_files(self):
        """فایل‌های تکراری را در گروه‌های جداگانه پیدا می‌کند."""
        file_hashes = {}
        total_files = sum([len(files) for _, _, files in os.walk(self.folder_path)])
        processed_files = 0

        # استفاده از tqdm برای نمایش نوار پیشرفت در ترمینال
        with tqdm(total=total_files, desc="Processing files", unit="file") as pbar:
            for root, _, files in os.walk(self.folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if not self._check_file_health(file_path):
                        continue  # رد کردن فایل‌های خراب یا خالی

                    file_hash = self._hash_file(file_path)
                    if file_hash:
                        file_hashes.setdefault(file_hash, []).append(file_path)

                    # آپدیت نوار پیشرفت
                    processed_files += 1
                    pbar.update(1)  # به‌روزرسانی نوار پیشرفت در ترمینال

                    if self.progress_bar:
                        progress_percentage = int((processed_files / total_files) * 100)
                        wx.CallAfter(self.progress_bar.SetValue, progress_percentage)
                        wx.CallAfter(self.progress_label.SetLabel, f"Progress: {progress_percentage}%")

        # برگرداندن گروه‌های فایل‌های تکراری
        return [group for group in file_hashes.values() if len(group) > 1]

    @staticmethod
    def _check_file_health(file_path):
        """Check if the file exists, is not empty, and is not a system file."""
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0
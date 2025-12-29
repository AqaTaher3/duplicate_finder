import os
import re
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor
import collections
from typing import List, Dict, Tuple, Set, Any
import wx
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileInfo:
    """کلاس نگهداری اطلاعات فایل"""
    path: str
    name: str
    normalized_name: str
    size: int
    extension: str
    mtime: float


class SimilarNameFinder:
    """کلاس یافتن فایل‌های با نام مشابه"""

    def __init__(self, folder_path: str, min_similarity: float = 0.7,
                 min_length: int = 10, use_cache: bool = True):
        """
        مقداردهی اولیه

        پارامترها:
            folder_path: مسیر پوشه
            min_similarity: حداقل شباهت (0-1)
            min_length: حداقل طول نام برای بررسی
            use_cache: استفاده از کش
        """
        self.folder_path = folder_path
        self.min_similarity = min_similarity
        self.min_length = min_length
        self.use_cache = use_cache

        self.results: List[List[str]] = []
        self.file_cache: Dict[str, FileInfo] = {}

        # تنظیمات پیش‌فرض برای نرمال‌سازی
        self.normalization_rules = [
            (r'\d+', ''),  # حذف اعداد
            (r'[^\w\s\-]', ''),  # حذف کاراکترهای خاص
            (r'\s+', ' '),  # جایگزینی فاصله‌های اضافه
        ]

        # کلمات متداول برای حذف
        self.common_words = {
            'official', 'version', 'remastered', 'remaster', 'original',
            'extended', 'clean', 'explicit', 'instrumental', 'acoustic',
            'live', 'studio', 'mix', 'edit', 'radio', 'single', 'album'
        }

    def _normalize_filename(self, filename: str) -> str:
        """نرمال‌سازی نام فایل"""
        # جدا کردن نام و پسوند
        name_part = Path(filename).stem.lower()

        # اعمال قوانین نرمال‌سازی
        for pattern, replacement in self.normalization_rules:
            name_part = re.sub(pattern, replacement, name_part)

        # حذف کلمات متداول
        words = name_part.split()
        filtered_words = [w for w in words if w not in self.common_words and len(w) > 2]

        # بازگرداندن رشته نرمال شده
        normalized = ' '.join(filtered_words).strip()

        return normalized

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """محاسبه شباهت بین دو رشته"""
        # استفاده از SequenceMatcher با تنظیمات بهینه
        return SequenceMatcher(None, str1, str2).ratio()

    def _get_file_info(self, file_path: str) -> FileInfo:
        """دریافت اطلاعات فایل"""
        try:
            # بررسی کش
            if self.use_cache and file_path in self.file_cache:
                return self.file_cache[file_path]

            # استخراج اطلاعات
            path_obj = Path(file_path)
            name = path_obj.name
            normalized_name = self._normalize_filename(name)

            stats = path_obj.stat()

            file_info = FileInfo(
                path=file_path,
                name=name,
                normalized_name=normalized_name,
                size=stats.st_size,
                extension=path_obj.suffix.lower(),
                mtime=stats.st_mtime
            )

            # ذخیره در کش
            if self.use_cache:
                self.file_cache[file_path] = file_info

            return file_info

        except Exception as e:
            print(f"❌ خطا در دریافت اطلاعات {file_path}: {e}")
            return None

    def _find_similar_groups(self, files_info: List[FileInfo]) -> List[List[str]]:
        """یافتن گروه‌های مشابه"""
        # گروه‌بندی بر اساس نام نرمال شده
        groups_by_name = collections.defaultdict(list)

        for file_info in files_info:
            if not file_info or len(file_info.normalized_name) < self.min_length:
                continue

            groups_by_name[file_info.normalized_name].append(file_info)

        # یافتن گروه‌های مشابه در هر گروه اصلی
        similar_groups = []

        for base_name, base_group in groups_by_name.items():
            if len(base_group) < 2:
                continue

            # بررسی شباهت درون گروه
            processed_paths = set()

            for i, file1 in enumerate(base_group):
                if file1.path in processed_paths:
                    continue

                current_group = [file1.path]
                processed_paths.add(file1.path)

                for j, file2 in enumerate(base_group[i + 1:], start=i + 1):
                    if file2.path in processed_paths:
                        continue

                    # محاسبه شباهت
                    similarity = self._calculate_similarity(file1.name, file2.name)

                    if similarity >= self.min_similarity:
                        current_group.append(file2.path)
                        processed_paths.add(file2.path)

                # اگر گروه بیش از یک عضو دارد، اضافه کن
                if len(current_group) > 1:
                    similar_groups.append(current_group)

        return similar_groups

    def find_similar_files(self, progress_callback=None) -> List[List[str]]:
        """یافتن فایل‌های با نام‌های مشابه"""
        all_files = []

        try:
            # جمع‌آوری تمام فایل‌ها
            for root, dirs, files in os.walk(self.folder_path):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    all_files.append(file_path)

            if not all_files:
                if progress_callback:
                    wx.CallAfter(progress_callback, 100, "❌ هیچ فایلی یافت نشد")
                return []

            # پردازش فایل‌ها
            files_info = []
            processed_count = 0

            with ThreadPoolExecutor(max_workers=8) as executor:
                future_to_file = {
                    executor.submit(self._get_file_info, file_path): file_path
                    for file_path in all_files
                }

                for future in future_to_file:
                    try:
                        file_info = future.result(timeout=5)
                        if file_info:
                            files_info.append(file_info)
                    except Exception as e:
                        print(f"❌ خطا در پردازش فایل: {e}")

                    processed_count += 1

                    # گزارش پیشرفت
                    if progress_callback and processed_count % 100 == 0:
                        progress = (processed_count / len(all_files)) * 100
                        wx.CallAfter(
                            progress_callback,
                            progress,
                            f"در حال پردازش: {processed_count}/{len(all_files)}"
                        )

            # یافتن گروه‌های مشابه
            similar_groups = self._find_similar_groups(files_info)

            # مرتب‌سازی بر اساس اندازه گروه (بزرگترین اول)
            similar_groups.sort(key=len, reverse=True)

            # گزارش نهایی
            if progress_callback:
                total_files = sum(len(g) for g in similar_groups)
                wx.CallAfter(
                    progress_callback,
                    100,
                    f"✅ یافت شد: {len(similar_groups)} گروه ({total_files} فایل)"
                )

            return similar_groups

        except Exception as e:
            print(f"❌ خطا در جستجوی فایل‌های مشابه: {e}")
            if progress_callback:
                wx.CallAfter(progress_callback, 100, f"❌ خطا: {str(e)}")
            return []

    def find_exact_name_matches(self) -> List[List[str]]:
        """یافتن فایل‌هایی که نام دقیقاً یکسان دارند (به جز پسوند)"""
        name_groups = collections.defaultdict(list)

        for root, dirs, files in os.walk(self.folder_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                name_without_ext = Path(filename).stem.lower()
                name_groups[name_without_ext].append(file_path)

        # فقط گروه‌هایی با بیش از یک فایل
        exact_matches = [group for group in name_groups.values() if len(group) > 1]

        return exact_matches

    def get_group_statistics(self, groups: List[List[str]]) -> Dict[str, Any]:
        """دریافت آمار گروه‌ها"""
        if not groups:
            return {}

        total_groups = len(groups)
        total_files = sum(len(g) for g in groups)
        avg_group_size = total_files / total_groups if total_groups > 0 else 0

        # توزیع اندازه گروه‌ها
        size_distribution = collections.Counter()
        for group in groups:
            size_distribution[len(group)] += 1

        return {
            'total_groups': total_groups,
            'total_files': total_files,
            'avg_group_size': avg_group_size,
            'size_distribution': dict(size_distribution),
            'largest_group': max(groups, key=len) if groups else [],
            'smallest_group': min(groups, key=len) if groups else []
        }
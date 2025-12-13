import os
import re
import itertools
from concurrent.futures import ThreadPoolExecutor
import collections
from difflib import SequenceMatcher
import wx


class SimilarNameFinder:
    def __init__(self, folder_path, min_similarity=0.7, min_length=10):
        self.folder_path = folder_path
        self.min_similarity = min_similarity  # از 0 تا 1
        self.min_length = min_length  # حداقل طول نام برای بررسی
        self.results = []

    def _normalize_filename(self, filename):
        """نرمال‌سازی نام فایل"""
        # حذف پسوند
        name = os.path.splitext(filename)[0]
        # حذف اعداد (اختیاری)
        name = re.sub(r'\d+', '', name)
        # حذف کاراکترهای خاص
        name = re.sub(r'[^\w\s]', '', name)
        # حذف فاصله‌های اضافه
        name = ' '.join(name.split())
        return name.strip().lower()

    def _calculate_similarity(self, str1, str2):
        """محاسبه شباهت بین دو رشته"""
        # استفاده از SequenceMatcher برای دقت بیشتر
        return SequenceMatcher(None, str1, str2).ratio()

    def _get_file_info(self, file_path):
        """دریافت اطلاعات کامل فایل"""
        try:
            size = os.path.getsize(file_path)
            name = os.path.basename(file_path)
            normalized_name = self._normalize_filename(name)
            return {
                'path': file_path,
                'name': name,
                'normalized_name': normalized_name,
                'size': size,
                'size_mb': size / (1024 * 1024),
                'extension': os.path.splitext(file_path)[1].lower()
            }
        except:
            return None

    def _find_similar_pairs(self, files_info):
        """یافتن جفت‌های مشابه"""
        similar_pairs = []
        files_by_normalized = collections.defaultdict(list)

        # گروه‌بندی بر اساس نام نرمال شده
        for file_info in files_info:
            if not file_info:
                continue
            norm_name = file_info['normalized_name']
            if len(norm_name) >= self.min_length:
                files_by_normalized[norm_name].append(file_info)

        # بررسی شباهت در هر گروه
        for norm_name, group in files_by_normalized.items():
            if len(group) < 2:
                continue

            # بررسی تمام ترکیب‌های دو تایی
            for file1, file2 in itertools.combinations(group, 2):
                similarity = self._calculate_similarity(
                    file1['name'], file2['name']
                )

                if similarity >= self.min_similarity:
                    # محاسبه تفاوت‌های اضافی
                    same_extension = file1['extension'] == file2['extension']
                    size_ratio = min(file1['size'], file2['size']) / max(file1['size'], file2['size']) if max(
                        file1['size'], file2['size']) > 0 else 0

                    similar_pairs.append({
                        'file1': file1,
                        'file2': file2,
                        'similarity': similarity,
                        'same_extension': same_extension,
                        'size_ratio': size_ratio,
                        'similarity_score': similarity * (1 if same_extension else 0.8) * size_ratio
                    })

        # مرتب‌سازی بر اساس امتیاز شباهت
        similar_pairs.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similar_pairs

    def find_similar_files(self, progress_callback=None):
        """یافتن فایل‌های با نام‌های مشابه"""
        all_files = []

        # جمع‌آوری تمام فایل‌ها
        for root, dirs, files in os.walk(self.folder_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                all_files.append(file_path)

        # پردازش موازی برای سرعت بیشتر
        files_info = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_file = {executor.submit(self._get_file_info, fp): fp for fp in all_files}

            for i, future in enumerate(future_to_file):
                try:
                    result = future.result()
                    if result:
                        files_info.append(result)
                except:
                    pass

                # گزارش پیشرفت
                if progress_callback and i % 100 == 0:
                    progress = (i + 1) / len(future_to_file) * 100
                    wx.CallAfter(progress_callback, progress, f"در حال بررسی {i + 1}/{len(all_files)} فایل...")

        # یافتن جفت‌های مشابه
        similar_pairs = self._find_similar_pairs(files_info)

        # تبدیل به گروه‌ها
        groups = self._pair_to_groups(similar_pairs)

        # گزارش نهایی
        if progress_callback:
            wx.CallAfter(progress_callback, 100, f"✅ یافت شد: {len(groups)} گروه فایل مشابه")

        return groups

    def _pair_to_groups(self, similar_pairs):
        """تبدیل جفت‌ها به گروه‌های مرتبط"""
        file_to_group = {}
        groups = []

        for pair in similar_pairs:
            file1_path = pair['file1']['path']
            file2_path = pair['file2']['path']

            if file1_path in file_to_group and file2_path in file_to_group:
                # هر دو در گروه‌های مختلف هستند - ادغام گروه‌ها
                group1_idx = file_to_group[file1_path]
                group2_idx = file_to_group[file2_path]
                if group1_idx != group2_idx:
                    groups[group1_idx].extend(groups[group2_idx])
                    for path in groups[group2_idx]:
                        file_to_group[path] = group1_idx
                    groups[group2_idx] = []

            elif file1_path in file_to_group:
                # فقط file1 در گروه است
                group_idx = file_to_group[file1_path]
                groups[group_idx].append(file2_path)
                file_to_group[file2_path] = group_idx

            elif file2_path in file_to_group:
                # فقط file2 در گروه است
                group_idx = file_to_group[file2_path]
                groups[group_idx].append(file1_path)
                file_to_group[file1_path] = group_idx

            else:
                # هیچ‌کدام در گروه نیستند
                new_group = [file1_path, file2_path]
                groups.append(new_group)
                group_idx = len(groups) - 1
                file_to_group[file1_path] = group_idx
                file_to_group[file2_path] = group_idx

        # حذف گروه‌های خالی و تکراری
        final_groups = []
        for group in groups:
            if group:
                unique_group = list(set(group))
                if len(unique_group) > 1:
                    final_groups.append(unique_group)

        return final_groups
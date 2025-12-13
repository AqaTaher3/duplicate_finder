import os
import time
import stat
import shutil
from src1.finder import FileFinder


class FileHandler:
    def __init__(self, folder_selected, priority_folder, keep_folder, auto_delete=True):
        self.folder_selected = folder_selected
        self.priority_folder = priority_folder
        self.keep_folder = keep_folder
        self.auto_delete = auto_delete
        self.current_set = 0
        self.selected_files = []
        self.file_sets = []
        self.failed_deletions = []  # لیست فایل‌هایی که حذف نشدند
        self.load_files()

    def load_files(self, prioritize_old=False):
        """بارگذاری فایل‌ها"""
        start_time = time.time()

        finder = FileFinder(self.folder_selected)
        self.file_sets = finder.find_files()

        if self.auto_delete:
            self.file_sets = self._apply_auto_deletion_rules(self.file_sets)

        print(f"زمان بارگذاری: {time.time() - start_time:.2f} ثانیه")
        return self.file_sets

    def _apply_auto_deletion_rules(self, file_sets):
        """اعمال قوانین حذف خودکار"""
        updated_sets = []
        deleted_count = 0

        for file_group in file_sets:
            if len(file_group) <= 1:
                updated_sets.append(file_group)
                continue

            keep_files = [f for f in file_group if self.keep_folder in f]
            priority_files = [f for f in file_group if self.priority_folder in f]
            other_files = [f for f in file_group if f not in keep_files and f not in priority_files]

            if keep_files:
                files_to_delete = [f for f in file_group if f not in keep_files]
                deleted_in_group = self._safe_delete_files(files_to_delete)
                deleted_count += deleted_in_group
                if deleted_in_group == len(files_to_delete):  # اگر همه حذف شدند
                    updated_sets.append(keep_files)
                else:
                    updated_sets.append([f for f in file_group if os.path.exists(f)])

            elif priority_files:
                deleted_in_group = self._safe_delete_files(priority_files)
                deleted_count += deleted_in_group
                remaining_files = [f for f in file_group if f not in priority_files or not os.path.exists(f)]
                if remaining_files:
                    updated_sets.append(remaining_files)
                else:
                    updated_sets.append([f for f in file_group if os.path.exists(f)])

            else:
                updated_sets.append(file_group)

        if deleted_count > 0:
            print(f"حذف خودکار: {deleted_count} فایل")

        return [group for group in updated_sets if group and all(os.path.exists(f) for f in group)]

    def _change_file_permissions(self, file_path):
        """تغییر permission فایل برای حذف"""
        try:
            if os.path.exists(file_path):
                # حذف attribute readonly
                os.chmod(file_path, stat.S_IWRITE)
                return True
        except Exception as e:
            print(f"خطا در تغییر permission فایل {file_path}: {e}")
        return False

    def _force_delete_file(self, file_path):
        """حذف اجباری فایل با روش‌های مختلف"""
        try:
            if not os.path.exists(file_path):
                return True

            # روش 1: حذف معمولی
            try:
                os.remove(file_path)
                return True
            except PermissionError:
                pass

            # روش 2: تغییر permission و حذف مجدد
            if self._change_file_permissions(file_path):
                try:
                    os.remove(file_path)
                    return True
                except PermissionError:
                    pass

            # روش 3: استفاده از shutil برای فایل‌های خاص
            try:
                os.chmod(file_path, stat.S_IWRITE)
                os.remove(file_path)
                return True
            except Exception:
                pass

            # روش 4: اگر پوشه است
            if os.path.isdir(file_path):
                try:
                    shutil.rmtree(file_path, ignore_errors=True)
                    return True
                except Exception:
                    pass

            return False

        except Exception as e:
            print(f"خطا در حذف اجباری {file_path}: {e}")
            return False

    def _safe_delete_files(self, files_to_delete):
        """حذف امن فایل‌ها با مدیریت خطا"""
        deleted_count = 0
        for file_path in files_to_delete:
            try:
                if not os.path.exists(file_path):
                    continue

                # ابتدا سعی می‌کنیم حذف معمولی
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"✅ حذف شد: {os.path.basename(file_path)}")
                    continue
                except PermissionError:
                    print(f"⚠️ دسترسی denied: {file_path} - تلاش برای حذف اجباری...")

                # اگر حذف معمولی نشد، حذف اجباری
                if self._force_delete_file(file_path):
                    deleted_count += 1
                    print(f"✅ حذف اجباری موفق: {os.path.basename(file_path)}")
                else:
                    print(f"❌ حذف ناموفق: {file_path}")
                    self.failed_deletions.append(file_path)

            except Exception as e:
                print(f"❌ خطا در حذف {file_path}: {e}")
                self.failed_deletions.append(file_path)

        return deleted_count

    def delete_files_silent(self, files_to_delete):
        """حذف فایل‌ها بدون نمایش پیام - برای پردازش دسته‌ای"""
        deleted_count = 0
        temp_failed = []

        for file_path in files_to_delete:
            try:
                if not os.path.exists(file_path):
                    continue

                try:
                    os.remove(file_path)
                    deleted_count += 1
                except PermissionError:
                    if self._force_delete_file(file_path):
                        deleted_count += 1
                    else:
                        temp_failed.append(file_path)
            except Exception:
                temp_failed.append(file_path)

        # اضافه کردن به لیست کلی خطاها
        self.failed_deletions.extend(temp_failed)
        return deleted_count

    def delete_selected_files(self, selected_files, prioritize_old=False):
        """حذف فایل‌های انتخاب شده"""
        if not selected_files:
            return

        deleted_count = self._safe_delete_files(selected_files)

        # نمایش فایل‌های ناموفق
        if self.failed_deletions:
            failed_list = "\n".join([os.path.basename(f) for f in self.failed_deletions[-10:]])  # آخرین 10 تا
            print(f"\n⚠️ فایل‌های حذف نشده ({len(self.failed_deletions)}):")
            print(failed_list)

        print(f"حذف دستی: {deleted_count} فایل از {len(selected_files)}")

        # بارگذاری مجدد لیست فایل‌ها
        self.load_files()

    def get_failed_deletions(self):
        """دریافت لیست فایل‌های حذف نشده"""
        return self.failed_deletions.copy()

    def clear_failed_deletions(self):
        """پاک کردن لیست فایل‌های حذف نشده"""
        self.failed_deletions.clear()

    def on_item_activated(self, file_path):
        if file_path in self.selected_files:
            self.selected_files.remove(file_path)
            print(f"File deselected: {file_path}")
        else:
            self.selected_files.append(file_path)
            print(f"File selected: {file_path}")

    def update_selected_count(self):
        return len(self.selected_files)

    def next_set(self):
        if self.current_set < len(self.file_sets) - 1:
            self.current_set += 1

    def back_to_previous_set(self):
        if self.current_set > 0:
            self.current_set -= 1

    def get_current_set_files(self):
        return self.file_sets[self.current_set] if self.current_set < len(self.file_sets) else []
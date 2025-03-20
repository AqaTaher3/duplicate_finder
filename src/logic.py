import os
import time
from tqdm import tqdm
from finder import FileFinder

class FileHandler:
    def __init__(self, folder_selected, priority_folder_name="000_PriorityFolder"):
        self.folder_selected = folder_selected
        self.priority_folder = os.path.join(folder_selected, priority_folder_name)  # مسیر فولدر اولویت‌دار برای حذف
        self.current_set = 0
        self.selected_files = []
        self.file_sets = []
        self.load_files()

    def load_files(self):
        """Load and group files using FileFinder, then auto-delete based on priorities."""
        finder = FileFinder(self.folder_selected)
        self.file_sets = finder.find_files()

        # بررسی و حذف خودکار فایل‌ها
        updated_file_sets = []
        for file_group in self.file_sets:
            if len(file_group) > 1:  # فقط گروه‌های تکراری رو بررسی کن
                priority_files = []  # فایل‌هایی که توی 000_PriorityFolder هستن
                non_priority_files = []  # فایل‌هایی که بیرون 000_PriorityFolder هستن

                # جدا کردن فایل‌های اولویت‌دار و غیراولویت‌دار
                for file in file_group:
                    if self.priority_folder in file:
                        priority_files.append(file)
                    else:
                        non_priority_files.append(file)

                if priority_files and non_priority_files:
                    # اگه هم فایل اولویت‌دار داریم هم غیراولویت‌دار، اولویت‌دارها حذف بشن
                    self.delete_selected_files(priority_files)
                    updated_file_sets.append(non_priority_files)
                elif priority_files and not non_priority_files:
                    # اگه همه فایل‌ها توی 000_PriorityFolder هستن، بر اساس تاریخ تغییر حذف کن
                    files_with_mtime = [(f, os.path.getmtime(f)) for f in priority_files if os.path.exists(f)]
                    if files_with_mtime:
                        # مرتب‌سازی بر اساس تاریخ تغییر (قدیمی‌ترها اول)
                        files_with_mtime.sort(key=lambda x: x[1])
                        # نگه داشتن جدیدترین فایل و حذف بقیه
                        files_to_delete = [f[0] for f in files_with_mtime[:-1]]  # همه به جز جدیدترین
                        if files_to_delete:
                            self.delete_selected_files(files_to_delete)
                        updated_file_sets.append([files_with_mtime[-1][0]])  # جدیدترین رو نگه دار
                    else:
                        updated_file_sets.append(file_group)  # اگه خطایی بود، گروه رو نگه دار
                else:
                    # اگه هیچ‌کدوم توی 000_PriorityFolder نبودن، گروه رو نگه دار
                    updated_file_sets.append(file_group)
            else:
                updated_file_sets.append(file_group)  # فایل‌های غیرتکراری رو نگه دار

        self.file_sets = updated_file_sets
        return self.file_sets

    def delete_selected_files(self, selected_files):
        """Deletes selected files and updates the file list."""
        for file in selected_files:
            print(f"Checking: {file}")
            try:
                if os.path.exists(file):
                    os.remove(file)
                    print(f"Deleted: {file}")
                else:
                    print(f"⚠️ File not found: {file}")
            except Exception as e:
                print(f"Error deleting {file}: {e}")

    # بقیه توابع بدون تغییر باقی می‌مونن
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
        return self.file_sets[self.current_set] if self.file_sets else []
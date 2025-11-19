import os
from src1.finder import FileFinder


class FileHandler:
    def __init__(self, folder_selected, priority_folder, keep_folder):
        self.folder_selected = folder_selected
        self.priority_folder = priority_folder  # مسیر فولدر اولویت‌دار برای حذف
        self.keep_folder = keep_folder  # مسیر فولدر اولویت‌دار برای نگه‌داری
        self.current_set = 0
        self.selected_files = []
        self.file_sets = []
        self.load_files()  # بارگذاری اولیه با اولویت‌های ثابت

    def load_files(self, prioritize_old=False):
        """Load files and apply auto-deletion for keep_folder and priority_folder priorities."""
        finder = FileFinder(self.folder_selected)
        self.file_sets = finder.find_files()  # دریافت لیست فایل‌های تکراری

        updated_file_sets = []
        for file_group in self.file_sets:
            if len(file_group) > 1:
                # دسته‌بندی فایل‌ها بر اساس اولویت‌ها
                keep_files = [f for f in file_group if self.keep_folder in f]
                priority_files = [f for f in file_group if self.priority_folder in f]
                other_files = [f for f in file_group if (self.keep_folder not in f) and (self.priority_folder not in f)]

                # منطق 1: اگر فایلی در keep_folder باشه، بقیه حذف بشن
                if keep_files:
                    files_to_delete = [f for f in file_group if f not in keep_files]
                    if files_to_delete:
                        self.delete_selected_files(files_to_delete)
                    updated_file_sets.append(keep_files)

                # منطق 2: اگر فایلی در priority_folder باشه، اون‌ها حذف بشن
                elif priority_files:
                    files_to_delete = priority_files
                    if files_to_delete:
                        self.delete_selected_files(files_to_delete)
                    updated_file_sets.append(other_files if other_files else file_group)

                # اگر هیچ‌کدوم از اولویت‌ها نبود، همه رو نگه دار
                else:
                    updated_file_sets.append(file_group)  # بدون حذف خودکار
            else:
                updated_file_sets.append(file_group)  # فایل‌های تکی رو نگه دار

        self.file_sets = updated_file_sets
        return self.file_sets

    def delete_selected_files(self, selected_files, prioritize_old=False):
        """Delete selected files with optional prioritization of older files."""
        if prioritize_old:
            # مرتب‌سازی فایل‌ها بر اساس تاریخ تغییر یا ایجاد (قدیمی‌ترها اول)
            files_with_time = []
            for f in selected_files:
                try:
                    mtime = os.path.getmtime(f) if os.path.exists(f) else float('inf')
                    ctime = os.path.getctime(f) if os.path.exists(f) else float('inf')
                    files_with_time.append((f, min(mtime, ctime)))
                except Exception as e:
                    print(f"Error getting time for {f}: {e}")
                    files_with_time.append((f, float('inf')))
            files_with_time.sort(key=lambda x: x[1])  # قدیمی‌ترها اول
            files_to_delete = [f[0] for f in files_with_time]
        else:
            files_to_delete = selected_files

        # حذف فایل‌ها
        for file in files_to_delete:
            print(f"Checking: {file}")
            try:
                if os.path.exists(file):
                    os.remove(file)
                    print(f"Deleted: {file}")
                else:
                    print(f"⚠️ File not found: {file}")
            except Exception as e:
                print(f"Error deleting {file}: {e}")

        # به‌روزرسانی file_sets بعد از حذف
        self.file_sets = [group for group in self.file_sets if group]  # حذف گروه‌های خالی
        for i, group in enumerate(self.file_sets):
            self.file_sets[i] = [f for f in group if f not in files_to_delete]

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
import os
from finder import FileFinder


class FileHandler:
    def __init__(self, folder_selected):
        self.folder_selected = folder_selected
        self.current_set = 0
        self.selected_files = []  # Store selected files
        self.file_sets = []  # List of files
        self.load_files()

    def load_files(self):
        files = []  # یا هر ساختار داده دیگری که برای ذخیره مسیرهای فایل نیاز داری
        try:
            # Logic برای بارگذاری فایل‌ها (برای مثال استفاده از os یا glob)
            # اینجا باید کدهای مربوط به جستجوی فایل‌ها قرار بگیرند
            for root, dirs, filenames in os.walk(self.folder_selected):
                for filename in filenames:
                    full_path = os.path.join(root, filename)
                    files.append(full_path)  # اضافه کردن مسیر فایل به لیست
            return files
        except Exception as e:
            print(f"Error loading files: {str(e)}")
            return None  # در صورت بروز خطا

    def delete_selected_files(self):
        for file in self.selected_files:
            try:
                os.remove(file)
                print(f"File ---------->  {file}  -----------> Deleted")
            except Exception as e:
                print(f"Error Deleting File: {file}\n{str(e)}")
        self.selected_files.clear()

    def on_item_activated(self, file_path):
        if file_path not in self.selected_files:
            self.selected_files.append(file_path)
        else:
            self.selected_files.remove(file_path)

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

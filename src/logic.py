import os
import sys
from tqdm import tqdm
from finder import FileFinder
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from finder import FileFinder


class FileHandler:
    def __init__(self, folder_selected):
        self.folder_selected = folder_selected
        self.current_set = 0
        self.selected_files = []  # ذخیره فایل‌های انتخاب‌شده
        self.file_sets = []  # لیست مجموعه‌های فایل
        self.load_files()

    def load_files(self):
        """بارگذاری فایل‌ها و گروه‌بندی آن‌ها با استفاده از FileFinder."""
        finder = FileFinder(self.folder_selected)
        self.file_sets = finder.find_files()
        return self.file_sets  # بازگرداندن فایل‌های گروه‌بندی‌شده

    def find_files(self):
        """بارگذاری فایل‌ها از پوشه‌ی انتخاب‌شده و نمایش نوار پیشرفت گرافیکی."""
        files = []
        try:
            file_list = []
            for root, _, filenames in os.walk(self.folder_selected):
                for filename in filenames:
                    file_list.append(os.path.join(root, filename))

            if not file_list:
                print("⚠️ No files found.")
                return

            # ✅ نمایش نوار پیشرفت گرافیکی با rich
            with Progress(
                TextColumn("[bold blue]🔍 Scanning files..."),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
                TimeRemainingColumn(),
                transient=True  # نوار پیشرفت بعد از اتمام حذف می‌شود
            ) as progress:
                task = progress.add_task("Processing", total=len(file_list))

                for file in file_list:
                    files.append(file)
                    progress.update(task, advance=1)

            # ✅ اگر لازم است، فایل‌ها را به‌صورت گروهی ذخیره کن
            if files:
                self.file_sets = [files]  # این قسمت را بر اساس نیاز تغییر دهید

        except Exception as e:
            print(f"⚠️ Error loading files: {str(e)}")


    def delete_selected_files(self):
        """ Deletes selected files and updates the file list. """
        for file in self.selected_files:
            try:
                os.remove(file)
                print(f"Deleted: {file}")
            except Exception as e:
                print(f"Error deleting {file}: {str(e)}")

        self.selected_files.clear()
        self.load_files()  # Reload files after deletion

    def on_item_activated(self, file_path):
        """ سلکت یا دیسلکت کردن فایل با فشردن کلید """
        if file_path in self.selected_files:
            self.selected_files.remove(file_path)  # اگر از قبل انتخاب شده، حذف کن
            print(f"File deselected: {file_path}")
        else:
            self.selected_files.append(file_path)  # در غیر این صورت اضافه کن
            print(f"File selected: {file_path}")

    def update_selected_count(self):
        """ Returns the number of selected files. """
        return len(self.selected_files)

    def next_set(self):
        """ Moves to the next set of files if available. """
        if self.current_set < len(self.file_sets) - 1:
            self.current_set += 1

    def back_to_previous_set(self):
        """ Moves back to the previous file set if possible. """
        if self.current_set > 0:
            self.current_set -= 1

    def get_current_set_files(self):
        """ Returns the current set of files. """
        return self.file_sets[self.current_set] if self.file_sets else []

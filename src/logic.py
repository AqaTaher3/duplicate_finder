import os
from tqdm import tqdm
from finder import FileFinder

class FileHandler:
    def __init__(self, folder_selected):
        self.folder_selected = folder_selected
        self.current_set = 0
        self.selected_files = []
        self.file_sets = []
        self.load_files()

    def load_files(self):
        """Load and group files using FileFinder."""
        finder = FileFinder(self.folder_selected)
        self.file_sets = finder.find_files()
        return self.file_sets

    def delete_selected_files(self, selected_files):
        """Deletes selected files and updates the file list."""
        for file in selected_files:
            print(f"Checking: {file}")  # چاپ مسیر فایل برای بررسی
            try:
                if os.path.exists(file):
                    os.remove(file)
                    print(f"Deleted: {file}")
                else:
                    print(f"⚠️ File not found: {file}")
            except Exception as e:
                print(f"Error deleting {file}: {e}")

        self.load_files()  # بارگذاری مجدد لیست

    def on_item_activated(self, file_path):
        """Select or deselect a file."""
        if file_path in self.selected_files:
            self.selected_files.remove(file_path)
            print(f"File deselected: {file_path}")
        else:
            self.selected_files.append(file_path)
            print(f"File selected: {file_path}")

    def update_selected_count(self):
        """Returns the number of selected files."""
        return len(self.selected_files)

    def next_set(self):
        """Moves to the next set of files if available."""
        if self.current_set < len(self.file_sets) - 1:
            self.current_set += 1

    def back_to_previous_set(self):
        """Moves back to the previous file set if possible."""
        if self.current_set > 0:
            self.current_set -= 1

    def get_current_set_files(self):
        """Returns the current set of files."""
        return self.file_sets[self.current_set] if self.file_sets else []
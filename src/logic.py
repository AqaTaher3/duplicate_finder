import os
from finder import FileFinder


class FileHandler:
    def __init__(self, folder_selected):
        self.folder_selected = folder_selected
        self.current_set = 0
        self.selected_files = []  # Store selected files
        self.file_sets = []  # List of file sets
        self.load_files()

    def load_files(self):
        """Load files and group them by hash using FileFinder."""
        finder = FileFinder(self.folder_selected)
        self.file_sets = finder.find_files()
        return self.file_sets  # Ensure this returns the grouped files

    def find_files(self):
        """ Loads files from the selected folder and groups them into sets if needed. """
        files = []
        try:
            for root, _, filenames in os.walk(self.folder_selected):
                for filename in filenames:
                    full_path = os.path.join(root, filename)
                    files.append(full_path)

            # If needed, group files into sets (e.g., by duplicates)
            if files:
                self.file_sets = [files]  # Modify this logic based on how sets should be structured

        except Exception as e:
            print(f"Error loading files: {str(e)}")

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

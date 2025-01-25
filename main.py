from tkinter import filedialog
from gui import show_duplicate_files


if __name__ == "__main__":
    folder_selected = filedialog.askdirectory(title="Select Folder")
    if folder_selected:
        show_duplicate_files(folder_selected)

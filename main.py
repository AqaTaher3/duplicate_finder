from tkinter import filedialog, messagebox
from gui import show_duplicate_files

if __name__ == "__main__":
    folder_selected = filedialog.askdirectory(title="Select Folder")

    if folder_selected:
        try:
            show_duplicate_files(folder_selected)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{e}")
    else:
        messagebox.showinfo("Info", "No folder selected. Please select a folder to continue.")

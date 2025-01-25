import os
import hashlib
import tkinter as tk
from tkinter import filedialog, ttk
from duplicate_finder import find_duplicates  # وارد کردن تابع find_duplicates

def select_folder():
    folder_selected = filedialog.askdirectory(title="Select a Folder")
    return folder_selected

def show_duplicate_files(folder_selected):
    root = tk.Tk()
    style = ttk.Style()
    style.configure("Treeview.Heading", foreground="white", background="#2e2e2e")

    root.title("Duplicate Files")
    root.geometry("800x600")
    root.configure(bg="#2e2e2e")

    label = ttk.Label(root, text="Duplicate files will be displayed here", font=("Arial", 15), foreground="white", background="#2e2e2e")
    label.pack(pady=20)

    progress_bar = ttk.Progressbar(root, length=400)
    progress_bar.pack(pady=20)
    progress_label_var = tk.StringVar()
    progress_label = ttk.Label(root, textvariable=progress_label_var, font=("Arial", 12), foreground="white", background="#2e2e2e")
    progress_label.pack(pady=10)

    tree = ttk.Treeview(root, columns=("path",), show="headings", height=15)
    tree.heading("path", text="File Path")
    tree.column("path", width=1200, anchor="w")
    tree.pack(padx=50, pady=20, expand=True, fill="both")

    label_var = tk.StringVar()
    label = ttk.Label(root, textvariable=label_var, font=("Arial", 15), foreground="white", background="#2e2e2e")
    label.pack(pady=20)

    duplicate_list = []
    current_set = 0
    files_deleted = 0

    def show_next_set():
        nonlocal duplicate_list, current_set, label_var, files_deleted
        if current_set < len(duplicate_list):
            files = duplicate_list[current_set]
            tree.delete(*tree.get_children())  # حذف تمام سطرهای قبلی
            for file in files:
                tree.insert("", "end", values=(file,))  # اضافه کردن فایل‌ها به Treeview
            label_var.set(f"Remaining duplicates: {len(duplicate_list) - current_set}")
        else:
            if files_deleted > 0:  # Only quit if files were deleted
                root.quit()

    def on_double_click(event):
        nonlocal duplicate_list, current_set, files_deleted
        selected_item = tree.selection()
        if selected_item:
            file_to_delete = tree.item(selected_item, "values")[0]
            os.remove(file_to_delete)
            tree.delete(selected_item)
            files_deleted += 1
            show_next_set()

    tree.bind("<Double-1>", on_double_click)

    def update_progress(progress, progress_bar, progress_label_var):
        root.after(0, lambda: progress_bar.configure(value=progress))
        root.after(0, lambda: progress_label_var.set(f"Progress: {int(progress)}%"))

    def run_find_duplicates():
        nonlocal duplicate_list, current_set
        duplicate_groups = find_duplicates(folder_selected, progress_bar, progress_label_var)  # حذف 'root'
        duplicate_list = list(duplicate_groups.values())
        current_set = 0
        label_var.set(f"Remaining duplicates: {len(duplicate_list)}")

        def process_duplicates():
            nonlocal current_set
            if current_set < len(duplicate_list) and len(duplicate_list[current_set]) > 1:
                show_next_set()
                current_set += 1
                root.after(500, process_duplicates)  # پردازش گام به گام

        root.after(500, process_duplicates)  # شروع پردازش به صورت گام به گام

    def skip_current_set():
        nonlocal current_set
        if current_set < len(duplicate_list):
            current_set += 1
            show_next_set()

    skip_button = ttk.Button(root, text="Skip", command=skip_current_set, width=20)
    skip_button.pack(pady=20)

    root.after(0, run_find_duplicates)

    root.mainloop()


if __name__ == "__main__":
    folder_selected = select_folder()

    if folder_selected:  # if folder is selected
        show_duplicate_files(folder_selected)

import os
from duplicate_finder import find_duplicates
import tkinter as tk
from tkinter import ttk

import threading


import os
from duplicate_finder import find_duplicates
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttk
import threading

def show_duplicate_files(folder_selected):
    root = tk.Tk()
    style = ttk.Style()
    # style.theme_use("classic")  # Use a different theme
    style.configure("Treeview.Heading", foreground="white", background="#2e2e2e")

    root.title("Duplicate Files")
    root.geometry("800x600")
    root.configure(bg="#2e2e2e")  # Dark background for the window

    label = ttk.Label(root, text="Duplicate files will be displayed here", font=("Arial", 15), foreground="white", background="#2e2e2e")
    label.pack(pady=20)

    progress_bar = ttk.Progressbar(root, length=400)
    progress_bar.pack(pady=20)
    progress_label_var = tk.StringVar()
    progress_label = ttk.Label(root, textvariable=progress_label_var, font=("Arial", 12), foreground="white", background="#2e2e2e")
    progress_label.pack(pady=10)

    tree = ttk.Treeview(root, columns=("path",), show="headings", height=15)
    tree.heading("path", text="File Path")  # no need to use style here
    tree.column("path", width=1200, anchor="w")
    tree.pack(padx=50, pady=20, expand=True, fill="both")

    label_var = tk.StringVar()
    label = ttk.Label(root, textvariable=label_var, font=("Arial", 15), foreground="white", background="#2e2e2e")
    label.pack(pady=20)

    duplicate_list = []
    current_set = 0

    def show_next_set():
        nonlocal duplicate_list, current_set, label_var
        if current_set < len(duplicate_list):
            files = duplicate_list[current_set]
            tree.delete(*tree.get_children())
            for file in files:
                tree.insert("", "end", values=(file,))
            current_set += 1
            label_var.set(f"Remaining duplicates: {len(duplicate_list) - current_set}")
        else:
            root.quit()

    def on_double_click(event):
        nonlocal duplicate_list, current_set
        selected_item = tree.selection()
        if selected_item:
            file_to_delete = tree.item(selected_item, "values")[0]
            os.remove(file_to_delete)
            tree.delete(selected_item)
            show_next_set()

    tree.bind("<Double-1>", on_double_click)

    def update_progress(progress, progress_bar, progress_label_var):
        # از root.after برای تغییرات در رشته اصلی استفاده می‌کنیم
        root.after(0, lambda: progress_bar.configure(value=progress))
        root.after(0, lambda: progress_label_var.set(f"Progress: {int(progress)}%"))

    def run_find_duplicates():
        nonlocal duplicate_list, current_set
        duplicate_groups = find_duplicates(folder_selected, progress_bar, progress_label_var, root)

        duplicate_list = list(duplicate_groups.values())
        current_set = 0

        label_var.set(f"Remaining duplicates: {len(duplicate_list)}")

        show_next_set()

    # Create a separate thread to run the duplicate finding function
    thread = threading.Thread(target=run_find_duplicates)
    thread.start()

    root.mainloop()

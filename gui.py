import os
import tkinter as tk
from tkinter import filedialog, ttk
from duplicate_finder import DuplicateFinder


def select_folder():
    return filedialog.askdirectory(title="Select a Folder")


def show_duplicate_files(folder_selected):
    root = tk.Tk()
    root.title("Duplicate Files")
    root.geometry("800x600")
    root.configure(bg="#2e2e2e")
    root.eval('tk::PlaceWindow . center')  # Center the window

    style = ttk.Style()
    style.configure("Treeview.Heading", foreground="white", background="#2e2e2e", font=("Arial", 14, "bold"))

    label = ttk.Label(root, text="Duplicate files will be displayed here", font=("Arial", 15), foreground="white",
                      background="#2e2e2e")
    label.pack(pady=10)

    progress_bar = ttk.Progressbar(root, length=500)
    progress_bar.pack(pady=10)
    progress_label_var = tk.StringVar()
    progress_label = ttk.Label(root, textvariable=progress_label_var, font=("Arial", 12), foreground="white",
                               background="#2e2e2e")
    progress_label.pack()

    tree = ttk.Treeview(root, columns=("path",), show="headings", height=15)
    tree.heading("path", text="File Path")
    tree.column("path", width=750, anchor="w")
    tree.pack(padx=20, pady=10, expand=True, fill="both")

    label_var = tk.StringVar()
    status_label = ttk.Label(root, textvariable=label_var, font=("Arial", 15), foreground="white", background="#2e2e2e")
    status_label.pack(pady=10)

    duplicate_list = []
    current_set = 0
    delete_count = {}

    def show_next_set():
        """Display the next set of duplicate files."""
        nonlocal duplicate_list, current_set, label_var
        if current_set < len(duplicate_list):
            tree.delete(*tree.get_children())
            for idx, file in enumerate(duplicate_list[current_set]):
                color = "#ff5555" if idx % 2 == 0 else "#ff9966"
                tree.insert("", "end", values=(file,), tags=(color,))
                tree.tag_configure(color, foreground=color)
            label_var.set(f"Duplicate sets remaining: {len(duplicate_list) - current_set}")
        else:
            label_var.set("No more duplicates. Review completed.")

    def on_double_click(event):
        """Delete file on double-click."""
        nonlocal duplicate_list, current_set, delete_count
        selected_item = tree.selection()
        if selected_item:
            file_to_delete = tree.item(selected_item, "values")[0]
            if file_to_delete in delete_count:
                delete_count[file_to_delete] += 1
            else:
                delete_count[file_to_delete] = 1

            if delete_count[file_to_delete] >= 2:
                os.remove(file_to_delete)
                tree.delete(selected_item)
                if len(tree.get_children()) == 1:
                    show_next_set()
            else:
                label_var.set("Click the file twice to confirm deletion.")

    tree.bind("<Double-1>", on_double_click)

    def run_find_duplicates():
        """Run duplicate file finder."""
        nonlocal duplicate_list, current_set
        finder = DuplicateFinder(folder_selected, progress_bar, progress_label_var)
        duplicate_groups = finder.find_duplicates()
        duplicate_list = list(duplicate_groups.values())

        if duplicate_list:
            label_var.set(f"Duplicate sets found: {len(duplicate_list)}")
            current_set = 0
            show_next_set()
        else:
            label_var.set("No duplicate files found.")

    def skip_current_set():
        """Skip the current set of duplicates."""
        nonlocal current_set
        if current_set < len(duplicate_list):
            current_set += 1
            show_next_set()

    def exit_program():
        """Safely exit the application."""
        root.quit()

    skip_button = ttk.Button(root, text="Skip", command=skip_current_set, width=20)
    skip_button.pack(pady=5)

    exit_button = ttk.Button(root, text="Exit", command=exit_program, width=20)
    exit_button.pack(pady=5)

    root.after(0, run_find_duplicates)
    root.mainloop()


if __name__ == "__main__":
    folder_selected = select_folder()
    if folder_selected:
        show_duplicate_files(folder_selected)

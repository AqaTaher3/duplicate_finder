import os


def making_folders(folder_selected):
    priority_folder = os.path.join(folder_selected, "000_PriorityFolder")
    corrupted_folder = os.path.join(folder_selected, "000_corrupted_folder")
    keep_folder = os.path.join(folder_selected, "000_keep_folder")

    os.makedirs(priority_folder, exist_ok=True)
    os.makedirs(corrupted_folder, exist_ok=True)
    os.makedirs(keep_folder, exist_ok=True)

    return [keep_folder, priority_folder, corrupted_folder]

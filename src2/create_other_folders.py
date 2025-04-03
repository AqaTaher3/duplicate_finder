import os


def making_folders():
    priority_folder = r"D:\000_Music\000_PriorityFolder"
    if not os.path.exists(priority_folder):
        os.makedirs(priority_folder, exist_ok=True)

    corrupted_folder = r"D:\000_Music\000_corrupted_forlder"
    if not os.path.exists(corrupted_folder):
        os.makedirs(corrupted_folder, exist_ok=True)
    return [priority_folder, corrupted_folder]
import os

def making_folders(folder_selected):
    base_000 = os.path.join(folder_selected, "000")
    priority_folder = os.path.join(base_000, "PriorityFolder")
    corrupted_folder = os.path.join(base_000, "Corrupted_folder")
    keep_folder = os.path.join(folder_selected, "000_Keep_folder")

    # اگر 000 وجود ندارد، بساز
    if not os.path.exists(base_000):
        os.makedirs(base_000)

    # اگر priority_folder وجود ندارد، بساز
    if not os.path.exists(priority_folder):
        os.makedirs(priority_folder)

    # اگر corrupted_folder وجود ندارد، بساز
    if not os.path.exists(corrupted_folder):
        os.makedirs(corrupted_folder)

    # اگر keep_folder وجود ندارد، بساز
    if not os.path.exists(keep_folder):
        os.makedirs(keep_folder)

    return [keep_folder, priority_folder, corrupted_folder]

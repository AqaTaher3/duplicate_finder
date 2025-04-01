import os


def delete_empty_folders(directory):
    print(f"Checking directory: {directory}")
    if not os.path.exists(directory):
        print("Directory does not exist!")
        return

    # First check if the main directory is empty
    if not os.listdir(directory):
        try:
            os.rmdir(directory)
            print(f"Deleted empty folder: {directory}")
        except OSError as e:
            print(f"Could not delete {directory}: {e}")

    # Now check for empty subfolders
    for foldername, subfolders, filenames in os.walk(directory, topdown=False):
        print(f"Checking folder: {foldername}")
        print(f"Subfolders: {subfolders}")
        print(f"Files: {filenames}")
        if not subfolders and not filenames:
            try:
                os.rmdir(foldername)
                print(f"Deleted empty folder: {foldername}")
            except OSError as e:
                print(f"Could not delete {foldername}: {e}")


dire = r"C:\Users\HP\Calibre Library\000_PriorityFolder"
delete_empty_folders(dire)

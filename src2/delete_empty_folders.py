import os


def delete_empty_folders(directory):
    print(f"Checking directory: {directory}")
    if not os.path.exists(directory):
        print("Directory does not exist!")
        return

    # Loop to keep deleting empty folders as long as they exist
    while True:
        # A flag to check if any folder was deleted
        folder_deleted = False

        # Check for empty subfolders in the directory
        for foldername, subfolders, filenames in os.walk(directory, topdown=False):
            print(f"Checking folder: {foldername}")
            print(f"Subfolders: {subfolders}")
            print(f"Files: {filenames}")
            if not subfolders and not filenames:
                try:
                    os.rmdir(foldername)
                    print(f"Deleted empty folder: {foldername}")
                    folder_deleted = True  # Mark that a folder was deleted
                except OSError as e:
                    print(f"Could not delete {foldername}: {e}")

        # If no folder was deleted in this cycle, stop
        if not folder_deleted:
            break

    # Finally, check and delete the main directory if it's empty
    if not os.listdir(directory):  # Check if the main directory is empty
        try:
            os.rmdir(directory)
            print(f"Deleted empty folder: {directory}")
        except OSError as e:
            print(f"Could not delete {directory}: {e}")

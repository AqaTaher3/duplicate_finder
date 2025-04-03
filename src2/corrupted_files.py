import os
import shutil
import subprocess
from tqdm import tqdm  # Import tqdm for progress bar


def check_file_integrity(file_path, ffmpeg_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False

    try:
        result = subprocess.run([ffmpeg_path, '-v', 'error', '-i', file_path, '-f', 'null', '-'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.returncode != 0  # اگر کد بازگشتی غیر صفر باشد، فایل خراب است
    except Exception as e:
        print(f"Error checking file {file_path}: {e}")
        return False


def move_corrupted_files(source_directory, ffmpeg_path, destination_directory):

    corrupted_files = []
    total_files = sum([len(files) for _, _, files in os.walk(source_directory)])  # Total number of files

    # Using tqdm to create the progress bar
    with tqdm(total=total_files, desc="Moving corrupted files", unit="file") as pbar:
        for root, dirs, files in os.walk(source_directory):
            for file in files:
                file_path = os.path.join(root, file)
                if check_file_integrity(file_path, ffmpeg_path):
                    dest_path = os.path.join(destination_directory, file)
                    shutil.move(file_path, dest_path)
                    print(f"Moved corrupted file: {file_path} -> {dest_path}")
                    corrupted_files.append(dest_path)

                pbar.update(1)  # Update progress bar for each file processed

    return corrupted_files


# source_dir = r"D:\000_Music"
# dest_dir = input("Enter destination directory (press Enter for default): ").strip()
# dest_dir = dest_dir if dest_dir else None
#
# move_corrupted_files(source_dir, dest_dir)

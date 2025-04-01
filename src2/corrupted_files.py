import os
import subprocess

def check_file_integrity(file_path):
    try:
        result = subprocess.run(['ffmpeg', '-v', 'error', '-i', file_path, '-f', 'null', '-'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(f"File is corrupted: {file_path}")
            return True  # فایل خراب است
    except Exception as e:
        print(f"Error checking file {file_path}: {e}")
    return False


def corrupted_files(directory):
    corrupted_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if check_file_integrity(file_path):
                print("corrupted file : ", file_path)
                corrupted_files.append(file_path)
    return corrupted_files


dire = r"C:\Users\G L S\Music\000_PriorityFolder\000_KHARAB"
corrupted_files(dire)


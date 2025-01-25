import os
import hashlib


def hash_file(file_path):
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        return None


def find_duplicates(folder_path, progress_bar, progress_label_var, root):
    file_hashes = {}
    duplicates = {}
    total_files = sum(len(files) for _, _, files in os.walk(folder_path))
    processed_files = 0

    for root_dir, _, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root_dir, file)
            file_hash = hash_file(file_path)
            processed_files += 1
            progress = (processed_files / total_files) * 100
            update_progress(progress, progress_bar, progress_label_var, root)
            if file_hash:
                if file_hash in file_hashes:
                    if file_hash not in duplicates:
                        duplicates[file_hash] = [file_hashes[file_hash]]
                    duplicates[file_hash].append(file_path)
                else:
                    file_hashes[file_hash] = file_path
    return duplicates


def update_progress(progress, progress_bar, progress_label_var, root):
    root.after(0, lambda: progress_bar.configure(value=progress))
    root.after(0, lambda: progress_label_var.set(f"Progress: {int(progress)}%"))



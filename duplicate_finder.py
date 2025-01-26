import os
import hashlib
from tkinter import ttk


class DuplicateFinder:
    def __init__(self, folder_path, progress_bar, progress_label_var):
        self.folder_path = folder_path
        self.progress_bar = progress_bar
        self.progress_label_var = progress_label_var
        self.file_hashes = {}
        self.duplicates = {}
        self.total_files = self._count_files()
        self.processed_files = 0

    def _count_files(self):
        """Count total number of files in the selected folder."""
        return sum(len(files) for _, _, files in os.walk(self.folder_path))

    def _hash_file(self, file_path):
        """Generate SHA-256 hash for the given file."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, IOError) as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def _update_progress(self):
        """Update progress bar and label."""
        if self.total_files == 0:
            self.progress_label_var.set("No files found.")
            return

        progress = (self.processed_files / self.total_files) * 100
        self.progress_bar.configure(value=progress)
        self.progress_label_var.set(f"Progress: {int(progress)}%")
        self.progress_bar.update_idletasks()

    def find_duplicates(self):
        """Find duplicate files based on hash values."""
        if self.total_files == 0:
            self.progress_label_var.set("No files to process.")
            return {}

        for root_dir, _, files in os.walk(self.folder_path):
            for file in files:
                file_path = os.path.join(root_dir, file)
                file_hash = self._hash_file(file_path)
                self.processed_files += 1
                self._update_progress()

                if file_hash:
                    if file_hash in self.file_hashes:
                        self.duplicates.setdefault(file_hash, [self.file_hashes[file_hash]]).append(file_path)
                    else:
                        self.file_hashes[file_hash] = file_path

        return self.duplicates

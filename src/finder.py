import os
import hashlib


class FileFinder:
    def __init__(self, folder_path, progress_bar=None, progress_label=None):
        self.folder_path = folder_path
        self.progress_bar = progress_bar
        self.progress_label = progress_label

    def _hash_file(self, file_path):
        """Generate SHA-256 hash for a file."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(8192):  # Read in chunks to handle large files
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, IOError) as e:
            print(f"Error reading file {file_path}: {str(e)}")
            return None

    def find_files(self):
        """Find files by comparing file hashes."""
        file_hashes = {}
        file_sets = {}
        total_files = sum([len(files) for _, _, files in os.walk(self.folder_path)])
        processed_files = 0

        for root, _, files in os.walk(self.folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                if not self._check_file_health(file_path):
                    continue  # Skip files that are empty or invalid

                file_hash = self._hash_file(file_path)
                if file_hash:
                    if file_hash in file_hashes:
                        file_sets.setdefault(file_hash, [file_hashes[file_hash]]).append(file_path)
                    else:
                        file_hashes[file_hash] = file_path

                # Update progress bar
                processed_files += 1
                if self.progress_bar:
                    progress_percentage = int((processed_files / total_files) * 100)
                    self.progress_bar.SetValue(progress_percentage)
                    self.progress_label.SetLabel(f"Progress: {progress_percentage}%")

        return file_sets

    @staticmethod
    def _check_file_health(file_path):
        """Check if the file exists and is not empty."""
        return os.path.exists(file_path) and os.path.getsize(file_path) > 0

